# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 17:18:05 2020

@author: stife
"""
#%% импорт всякого

import cv2
import matplotlib.pyplot as plt
import numpy as np

#%% подключение компьютерного зрения

key = "6d3f040092754db0bd8b74bbb8f4b0ea"
endpoint = "https://westcentralus.api.cognitive.microsoft.com"

import azure.cognitiveservices.vision.face as cf
from msrest.authentication import CognitiveServicesCredentials
cli = cf.FaceClient(endpoint, CognitiveServicesCredentials(key))

#%% загрузка в массив и получение лицевых меток

path2image = "images/gates/gates_1.jpg"

def imread(fn):
    im = cv2.imread(fn)
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB) if im is not None else None

image = imread(path2image)
with open(path2image, "rb") as f:
    imagepoints = cli.face.detect_with_stream(f, return_face_landmarks=True)[0].face_landmarks.as_dict()

plt.imshow(image)
plt.axis("off")

#%% масштабирование с фиксированным уровнем для рта

target_triangle = np.float32([[130.0, 120.0], [170.0, 120.0], [150.0, 160.0]])
size = 300

def affine_transform(img, attrs):
    mc_x = (attrs["mouth_left"]["x"] + attrs["mouth_right"]["x"]) / 2.0
    mc_y = (attrs["mouth_left"]["y"] + attrs["mouth_right"]["y"]) / 2.0
    tr = cv2.getAffineTransform(np.float32([(attrs["pupil_left"]["x"], attrs["pupil_left"]["y"]),
                                            (attrs["pupil_right"]["x"], attrs["pupil_right"]["y"]),
                                            (mc_x, mc_y)]), target_triangle)                                
    return cv2.warpAffine(img, tr, (size,size))

image = affine_transform(image, imagepoints)

plt.imshow(image)
plt.axis("off")

#%% отражения

def display_images(l):
    n = len(l)
    fig,ax = plt.subplots(1, n)
    for i,im in enumerate(l):
        ax[i].imshow(im)
        ax[i].axis('off')
    fig.set_size_inches(fig.get_size_inches() * n)
    plt.tight_layout()
    plt.show()

flip_image0 = cv2.flip(image, 0) # отражение по вертикали
flip_image1 = cv2.flip(flip_image0, 1)
flip_image2 = cv2.flip(image, 1) # отражение по горизонтали

images = [image, flip_image0, flip_image1, flip_image2]

display_images(images)

#%% смешивание

def merge(imgs):
    return (np.average(np.array(imgs) / 255., axis=0) * 255).astype(np.ubyte)

res = merge(images)
plt.imshow(res)
plt.axis("off")

#%% эффект акварелизация (фильтр) по вкусу

M = np.array([[1, 2, 1],
              [2, 4, 2],
              [1, 2, 1]]) / 16

R = np.array([[-0.5, -0.5, -0.5],
              [-0.5, 5, -0.5],
              [-0.5, -0.5, -0.5]])

def apply_filter(image, mat_filter, norm=True):
    res = np.zeros(shape=image.shape, dtype=np.float32)
    for i in range(1, image.shape[0] - 1):
        for j in range(1, image.shape[1] - 1):
            for k in range(image.shape[2]):
                res[i, j, k] = np.sum(image[i - 1: i + 2, j - 1: j + 2, k] * mat_filter)
    return normalize(res) if norm else res

def normalize(image):
    image = np.where(image > 255, 255 * np.ones_like(image), image)
    image = np.where(image < 0, np.zeros_like(image), image)
    return np.uint8(image)

def aquarelle_filter(image):
    image = apply_filter(image, M, norm=False)
    image = apply_filter(image, R)
    return image
      
aqua_res = aquarelle_filter(res.copy())
        
plt.imshow(aqua_res)
plt.axis("off")

#%% сохранение
        
cv2.imwrite("results/two_gates.jpg", cv2.cvtColor(aqua_res, cv2.COLOR_BGR2RGB))