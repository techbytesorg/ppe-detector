![GitHub User's stars](https://img.shields.io/github/stars/nosterdream/hard-hat-detection-2)
![GitHub forks](https://img.shields.io/github/forks/nosterdream/hard-hat-detection-2)
<a href="https://universe.roboflow.com/nosterdream-07kam/hard-hat-detection-nmvjs">
    <img src="https://app.roboflow.com/images/download-dataset-badge.svg"></img>
</a>
<a href="https://universe.roboflow.com/nosterdream-07kam/hard-hat-detection-nmvjs/model/">
    <img src="https://app.roboflow.com/images/try-model-badge.svg"></img>
</a>

# Hard hat Detection YOLO11
## Overview

This is the second iteration of the [previous hard hat detection project](https://github.com/nosterdream/hard-hat-detection).
Key features of new version:
- new detection model (YOLO11 vs YOLOv8)
- one detection model for all objects in a frame (person, head and hard hat)
- better performance
- webcam support

This project focuses on detecting hard hats on individuals in videos. Leveraging the power of the YOLO11 model, the system is capable of identifying people and determining if they are wearing hard hats. The output is an annotated video where detected people, heads and hard hats are highlighted with bounding boxes. If a person is wearing a hard hat, the bounding box around them will be green, otherwise, it will be red.


## Table of Contents

- [Requirements](#requirements)
- [Model and Dataset](#model)
- [Installation](#installation)
- [Usage](#usage)
- [Training](#training)
- [Contributing](#contributing)
- [License](#license)

## Requirements

- Python 3.11
- Ultralytics 8.3.70
- OpenCV 4.11.0.86
- Torch 2.3.0+cu121
- Torchvision 0.18.0+cu121

## Model

You can find the model here - [link](https://drive.google.com/drive/folders/1gEfCcMj3T4jzhoEygjBgu8K_ylkoKvsw?usp=sharing).
The model "hardhat_detection_yolo11_200_epochs_best_02032025.pt" have to be in the directory ".\models".
It was trained in the Kaggle notebook.

The custom dataset was made on Roboflow. You can find it by clicking on the badge "Download Dataset" above.
You can also try <ins>the other model</ins> that was trained on Roboflow. Just click on the badge "Try Model" above.

## Installation

To run this project, you need to have Python 3.11 installed. Follow these steps to set up the environment:

1. Clone the repository:
    ```bash
    git clone https://github.com/nosterdream/hard-hat-detection-2.git
    cd hardhat-detection
    ```

2. Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

To read the video, you have to specify `video_path` to your video file:

```Python
video_path = "input_files\hardhat_input_video.mp4"
```

To run the hard hat detection on the webcam you have to use 0 for video_path:

```Python
video_path = 0
```

Then just run main.py script and you'll see annotated images on the screen. After script ends the annotated video will be automatically saved in the ".\output_files" directory with the name "processed.mp4"

## Training

You'll definitely need to train the model on your own dataset for better results in your application.
So, just follow these steps:
1. Upload your dataset on Roboflow https://universe.roboflow.com/
2. Annotate images with classes (person, head and hardhat)
3. Change the code cell in the ".\training\download_and_train.ipynb" and run it to get dataset:

```Python
# Download the dataset from Roboflow Example
from roboflow import Roboflow

rf = Roboflow(api_key="YOUR_API_KEY")
project = rf.workspace("your-login").project("project-name")
version = project.version(project-version)
dataset = version.download("yolov11")
```
4. Run the following cell code, specifying the path to .yaml file, the number of epochs and the image size:

```Python
# Train the YOLO11 model for 200 epochs
from ultralytics import YOLO

model = YOLO('./models/hardhat_detection_yolo11_200_epochs_best_02032025.pt')
results = model.train(
    data="path-to-data.yaml", 
    epochs=200, 
    imgsz=640,
    batch=0.9,
    resume=True,
    device=0
)
```
5. You can find the result in runs/detect/train/weights/.

This will train the YOLOv8 model on your dataset.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request if you have any improvements or bug fixes.

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a Pull Request.

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.

---

For any questions or issues, please open an issue on GitHub or contact the project maintainer at novoselov.g.v@mail.ru.

---
