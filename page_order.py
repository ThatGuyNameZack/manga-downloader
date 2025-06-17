import os

def rename_images_in_folder(folder_path):
    files = sorted(os.listdir(folder_path))
    for i, filename in enumerate(files):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            new_name = f"{i+1:03}.jpg"
            new_path = os.path.join(folder_path, new_name)
            os.rename(file_path, new_path)
    print(f"Renamed {len(files)} files in {folder_path} to be in order in numbers.")