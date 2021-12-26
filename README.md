# Build own render farm (Experimental Code)

Rendering on Cloud Computing Services (Currently Azure Only).

## Using Azure Batch
In azure directory, the script setup Blender 3.0 on Azure Batch Server, and create a task for rendering.

### Setup

1. Sign in Azure Portal and create Batch
1. Install python (3.9.X) before run.
1. Rename settins.py.example to settings.py, and update keys in the file.
1. create directory azure/files. The files are automatically upload to server in ```files``` directory
    - /azure
        - create_pool_job.py
        - settings.py
        - files
            - (put files like .blender)
    - README.md
    - ..

### Run the script

First, create a pool and nodes with Blender 3.0.
```
python create_pool_job.py pool
```

Next, run rendering with following command.

```
python create_pool_job.py task test.blend
```

After, Please check the result on Azure Portal.

# Related Softwares
- Blender
    - https://www.blender.org/

# References
- Microsoft's Documents
    - https://docs.microsoft.com/en-us/azure/batch/
    - https://docs.microsoft.com/en-us/azure/batch/quick-run-python
    - https://docs.microsoft.com/en-us/azure/batch/tutorial-parallel-python
