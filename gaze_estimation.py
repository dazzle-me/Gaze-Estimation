from FaceAligner import FaceAligner
from FaceAligner import rect_to_bb

from modules.SpaNet import SpaNet
from modules.ResGaze import ResGaze

from src.view_data import draw_gaze

import torchvision.transforms as transforms

import torch

import argparse
import imutils
import dlib
import cv2
import time

from copy import copy


def load_model(device):
    # model = SpaNet(in_features=64, middle_features=32, residual_count=3, use_batchnorm=3)
    # model.load_state_dict(torch.load('models/SpaNet_1/SpaNet_unique_id_5_epoch_1_step_24000.pth'))
    model = ResGaze().to(device)
    model.load_state_dict(torch.load('weights/Resnet50_unique_id_1_epoch_11_step_9000.pth', map_location=device))
    return model

def equalize_hists(face_patch):
    img_yuv = cv2.cvtColor(face_patch, cv2.COLOR_BGR2YUV)
    img_yuv[:, :, 0] = cv2.equalizeHist(img_yuv[:, :, 0])
    return cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
    
def swap_channels(image):
    return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

def smooth_gaze(gaze, previous_gaze, gaze_smoothing=0.4):
    if previous_gaze is not None:
        return gaze_smoothing * previous_gaze + gaze * (1 - gaze_smoothing)
    return gaze 

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--shape-predictor", default='weights/shape_predictor_68_face_landmarks.dat', help = "Path to facial landmark predictor")
    args = vars(ap.parse_args())

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(args["shape_predictor"])
    
    use_gpu = True
    device = "cuda:0" if torch.cuda.is_available() and use_gpu else "cpu"

    gaze_estimator = load_model(device) 
    gaze_estimator.eval()

    to_tensor = transforms.Compose([
        transforms.Lambda(lambda x : swap_channels(x)),
        transforms.Lambda(lambda x : equalize_hists(x)),
        transforms.ToTensor()
    ])

    fa = FaceAligner(predictor, desiredFaceWidth=224)

    video = cv2.VideoCapture(0)

    start_time = time.time()
    frames = 0
    previous_gaze = None
    face_with_predicted_gaze = None

    draw_normalized_gaze = True
    draw_input_gaze = True
    verbose = False
    show_fps = True
    while(True):
        ret, image = video.read()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        start_time = time.time()
        rects = detector(gray, 0)
        cuda_faceAligned = None
        for rect in rects:
            (x, y, w, h) = rect_to_bb(rect)
            faceOrig = image[y : y + h, x : x + w]
            faceAligned, affine_center, affine_matrix = fa.align(image, gray, rect, verbose=verbose)
            with torch.no_grad():
                cuda_faceAligned = to_tensor(faceAligned).to(device)
                cuda_faceAligned = torch.unsqueeze(cuda_faceAligned, 0)
                cuda_gaze = gaze_estimator(cuda_faceAligned)
                
                gaze = smooth_gaze(cuda_gaze.detach().cpu().numpy().copy()[0], previous_gaze, gaze_smoothing=0.4)
                previous_gaze = copy(gaze)
                
            inverted_affine_transform = cv2.invertAffineTransform(affine_matrix)
            if draw_normalized_gaze:
                faceAligned = draw_gaze(faceAligned, gaze, prediction=True, original=False)
            if draw_input_gaze: 
                image = draw_gaze(image, gaze, prediction=True, offset=affine_center, transform=inverted_affine_transform, image_shape=faceAligned.shape, original=True)
        if show_fps:
            fps = 1 / (time.time() - start_time)
            fps = str(int(fps))
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(image, "FPS : {}".format(fps), (7, 30), font, 1, (255, 100, 0), 3, cv2.LINE_AA) 
        
        cv2.imshow("Input", image)
        cv2.imshow("Aligned", faceAligned)
        key = cv2.waitKey(1) & 0xFF
        frames += 1
        if key == ord('q'):
            break
        elif key == ord('n'):
            draw_normalized_gaze ^= True
        elif key == ord('i'):
            draw_input_gaze ^= True
        elif key == ord('v'):
            verbose ^= True 
        elif key == ord('f'):
            show_fps ^= True       
if __name__ == '__main__':
    main()
