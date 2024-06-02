# Plant Disease Detection using PyTorch, Flask, and Streamlit

This project aims to detect plant diseases using deep learning techniques implemented with PyTorch. It provides both a web application built with Flask for real-time detection and a user-friendly interface powered by Streamlit for offline analysis.

## Dataset
The dataset used in this project is available on Hugging Face: [Plant Disease Dataset](https://huggingface.co/datasets/khushwant04/Plant-Disease-Dataset)

## Docker Image
You can find the Docker image containing the complete working environment and application at Docker Hub: [Plant Disease Detection Docker Image](https://hub.docker.com/repository/docker/khushwant04/plant-disease/)

## Features
- Utilizes PyTorch and torchvision for training and deploying deep learning models.
- Provides a Flask API for real-time inference.
- Offers a Streamlit web application for offline analysis and visualization.
- Supports a wide range of plant diseases for accurate detection.

## Project Structure
- `model`: Directory containing trained models.
- `src`: Directory containing the source code.
  - `Models`: Model dir
    - `resnet.py`: Implementation of ResNET from scratch.
  - `datasets`: Directory for deep learning model scripts.
    - `plant_disease.py`: script for creating custom dataset.
  - `helper.py`: script which contains helperfunctions.
  - `train.py`: script for training loop and class.
- `.gitignore`: File specifying ignored files and directories for version control.
- `README.md`: This README file.
- `dockerfile`: Dockerfile for building Docker image.
- `main.ipynb`: Jupyter notebook containing main code or experiments.
- `main.py`: Main Python script for running the application.
- `requirements.txt`: File specifying project dependencies.

## Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/khushwant04/Plant-Disease.git

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
3. Run the Streamlit app:
   ```bash
   streamlit run main.py
   
## Testing images:
   [Download Testing Images](https://1drv.ms/f/s!Akr767JWN3vEllsH0PqUESUpbakN?e=rETLSX).
   ```bash
   https://1drv.ms/f/s!Akr767JWN3vEllsH0PqUESUpbakN?e=rETLSX


