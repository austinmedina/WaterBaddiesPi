import cv2

if __name__ == "__main__":
    for i in range(30):
        try:
            cap = cv2.VideoCapture(i)
            if not cap.isOpened():
                print("Error opening video stream or file")
                raise Exception("Couldnt open microscope stream")
            
            ret, frame = cap.read()

            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                raise Exception("Couldnt open microscope picture frame")
            
            print(f"WE FOUND IT AT {i}")
        except:
            continue
        
        