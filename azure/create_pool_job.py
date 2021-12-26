# 2021/12/25 maemaewater
import azure.batch as batch
import azure.batch.batch_auth as batchauth
import azure.batch.models as batchmodels
import os
import sys
from azure.storage.blob import BlobServiceClient
from pathlib import Path
import time
import settings

account = settings.account
key = settings.key
batch_url = settings.batch_url
storage_connection_string = settings.storage_connection_string

pool_id = "LinuxNodesBlender"
vm_size = "STANDARD_D2_V3"
node_count = 1

def create_client():
  creds = batchauth.SharedKeyCredentials(account, key)
  config = batch.BatchServiceClientConfiguration(creds, batch_url)
  client = batch.BatchServiceClient(creds, batch_url)

  return client

def create_pool():
  client = create_client()
  new_pool = batchmodels.PoolAddParameter(id=pool_id, vm_size=vm_size)
  new_pool.target_dedicated_nodes = node_count

  user = batchmodels.UserIdentity(
    auto_user=batchmodels.AutoUserSpecification(
      elevation_level=batchmodels.ElevationLevel.admin,
      scope="pool"
    )
  )

  commands = [
    "pwd",
    "apt install -y -qq libxi-dev libxxf86vm-dev libxrender-dev",
    "wget https://mirror.clarkson.edu/blender/release/Blender3.0/blender-3.0.0-linux-x64.tar.xz",
    "tar Jxfv blender-3.0.0-linux-x64.tar.xz",
    "cp -r $AZ_BATCH_NODE_STARTUP_DIR/wd/blender-3.0.0-linux-x64 $AZ_BATCH_NODE_STARTUP_DIR/blender"
  ]

  command_line = "/bin/sh -c \"" + "; ".join(commands) + "\""

  print(command_line)

  start_task = batchmodels.StartTask(command_line=command_line, user_identity=user)
  start_task.run_elevated = True
  new_pool.start_task = start_task


  images = client.account.list_supported_images()
  #for img in images:
  #  print('[image]: {0}, {1}, {2}'.format(img.image_reference.publisher, img.image_reference.offer, img.image_reference.sku))

  ir = batchmodels.ImageReference(
    publisher="canonical",
    offer="0001-com-ubuntu-server-focal",
    sku="20_04-lts",
    version="latest"
    )

  vmc = batchmodels.VirtualMachineConfiguration(
    image_reference=ir,
    node_agent_sku_id="batch.node.ubuntu 20.04"
    )

  new_pool.virtual_machine_configuration = vmc

  client.pool.add(new_pool)


def create_task(n, blend_file_name):
  client = create_client()

  path = Path('files')
  files = list(path.glob("*"))

  input_file_paths = list(path.glob("*"))

  for f in input_file_paths:
    print("copy to storage: {0}".format(f))

  blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)
  container_client = blob_service_client.get_container_client('blender')

  input_files = []

  for i in input_file_paths:
    name = Path(i).name
    
    blob = blob_service_client.get_blob_client("blender", name)
    with open(i, "rb") as data:
      blob.upload_blob(data, overwrite=True)
      input_files.append(batchmodels.ResourceFile(auto_storage_container_name="blender"))

  job_id = 'render_job_' + n
  job = batchmodels.JobAddParameter(
    id=job_id,
    pool_info=batch.models.PoolInformation(pool_id=pool_id)
  )

  client.job.add(job)

  tasks = list()

  commands = "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$AZ_BATCH_NODE_STARTUP_DIR/blender/lib; $AZ_BATCH_NODE_STARTUP_DIR/blender/blender -b " + blend_file_name + " -o $AZ_BATCH_TASK_DIR/frame_##### -f 1"
  command = "/bin/sh -c \"" + commands + "\""

  tasks.append(batchmodels.TaskAddParameter(
    id="Task_" + n,
    command_line = command,
    resource_files=[input_files[0]]
  ))

  client.task.add_collection(job_id, tasks)
  print("[job_id]: {0}".format(job_id))



if __name__ == "__main__":
  args = sys.argv
  if len(args) < 2:
    print('please set command type: pool or task')
    exit()

  command_type = args[1]

  if command_type == "pool":
    create_pool()

  if command_type == "task":
    if len(args) < 3:
      print('please set .blend file name: task add_to_task.blend')
      exit()

    create_task(str(time.time_ns()), args[2])

  print('[ok]')

