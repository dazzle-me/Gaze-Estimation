# GazeEstimation
This README contains my attempts to solve gaze estimation task.

dlib + Pytorch pipeline for gaze estimation.

`SynthesEyes.ipynb` contains step-by-step implementation of 
training environment for [SynthesEyes](https://www.cl.cam.ac.uk/research/rainbow/projects/syntheseyes/) dataset.

`Hourglass.ipynb` contains my implementation of Hourglass neural network, it's training and evaluation for pupil heatmaps extraction.

`Gaze-Estimation-using-XGaze-dataset.ipynb` contains training environment used in order to train and test ResGaze model on XGaze dataset.

## Gaze estimation
| Model                                  | Test Error                    |   Train size/Amount of epochs |   Model size   |
|:---------------------------------------|:-----------------------------:|:-----------------------------:|:---------------|
| GazeNet (7 conv, 1 dense, w/o BN)      |           0.91                |       10240/70                |    8.7 Mb      |
| GazeNet_v2 (7 conv, 2 dense, w/ BN)    |           0.79                |       10240/70                |   15.6 Mb      |

### GazeNet (7 conv, 1 dense, w/o BN) 
Test error is quite big because it represents L1 loss with respect to euler's angles in screen space 
(yaw and pitch, reference point located at pupil center) 

### GazeNet_v2 (8 conv, 2 dense, w/ BN)
Clear underfit, my guess is that it is pretty hard to learn direct mapping from feature space of the image (HxWx3) directly to gaze (just 2 features, it is either point on the screen or two angles in radians). Should try to learn intermediate features first.

UPD : Legend are not right, it must be "Train loss and test loss" 

![](learning_curves/GazeNet_v2.jpg)

## Pupil landmarks estimation

| Model                                  | Test Error                    | Train size/Amount of epochs |   Model size   | Evaluation time |
|:---------------------------------------|:-----------------------------:|:---------------------------:|:---------------|:----------------|
| PupilNet-3Hourglass w/ BN              |              ~3000            |     10240/153               |       2 Mb     | 52 ms on pretty old InterCore-i5 CPU   |

### PupilNet-3Hourglass-sigma_10 w/ BN

Test error is around 3000, which is actually 3000 / 32 ~ 93.75 per prediction, because I accidentally 
measured it over batch, not over single image. It means that following model gives approximately less than 0.01 error per pixel 
(because one prediction contains 8 heatmaps each of them has 80x120 pixels), which 
is enough to predict valuable heatmaps.

![](learning_curves/PupilEyeNet_3Hourglass.jpg)

Actual heatmaps of pupil landmarks : 

![](networks_evaluations/pupil_heatmaps.png)

### ResGaze

| Model                                  | Test Error                    | Train size/Amount of epochs |   Model size   | Evaluation time |
|:---------------------------------------|:-----------------------------:|:---------------------------:|:---------------|:----------------|
| ResGaze (resnet50 as a backbone + regressor from extracted features)   |             2 degrees (angular error derived from cosine similarity) on XGaze dataset         |     750k/10               |       100 Mb     | 10ms on RTX 3060Ti per sample   |

This simple model is inspired by [RT-GENE](https://openaccess.thecvf.com/content_ECCV_2018/papers/Tobias_Fischer_RT-GENE_Real-Time_Eye_ECCV_2018_paper.pdf) paper, where they used VGG-16 network for feature extraction, and I decided to use Resnet50 to do the job. 

Next pretty import thing, that [XGaze](https://ait.ethz.ch/projects/2020/ETH-XGaze/) dataset was used to train robust gaze predictor. Is was said, that the model was able to achieve angular error of 2 degrees per sample, which is impressive, because this dataset has very rich distribution in sense of head and gaze rotations. 

Train predictions (green is the prediction and blue is a ground truth gaze vector)             |  Test predictons
:-------------------------:|:-------------------------:
![Train predictions](networks_evaluations/ResGaze_train_predictions.jpg)|  ![Test predictons](networks_evaluations/ResGaze_test_predictions.jpg)

## ToDo

• <s> Use pupil features given in the dataset </s> 

• <s> Implement pupil center detection using another dense layer (probably it is just weighted softmax of all heatmaps?) </s>

• Apply augmentation <s> <b> only if </b> model works bad during inference time </s> 

Just took a look at learning curves, model is too weak, so
I think we need stronger feature extraction

• <s> Implement hourglass </s> 

• <s> Explain hourglass error </s>

• <s> Implement softmax over heatmaps in order to predict landmarks coordinates </s>
