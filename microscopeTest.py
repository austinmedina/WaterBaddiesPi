import cv2

# Initialize the camera
cap = cv2.VideoCapture(0)  # 0 usually refers to the first USB camera

# Check if the camera is opened successfully
if not cap.isOpened():
    print("Error opening video stream or file")

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    # If frame is read correctly, ret is True
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break

    # Display the resulting frame
    cv2.imshow('frame', frame)

    # Press 'q' to exit
    if cv2.waitKey(1) == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()