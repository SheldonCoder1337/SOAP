FROM pytorch/pytorch:2.4.1-cuda11.8-cudnn9-runtime

WORKDIR /app

COPY ../requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN pip install gunicorn

COPY ../src /app/src

# If you encounter the following issues:
# ImportError: libGL.so.1: cannot open shared object file: No such file or directory
# ImportError: libgthread-2.0.so.0: cannot open shared object file: No such file or directory
# Please uncomment the following line and reconstruct the image
# See: 
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0

# Set the environment variables 
# If you want to use local model, please uncomment the following line and modify the path 
ENV MODEL_ROOT_DIR=/hdd/models
