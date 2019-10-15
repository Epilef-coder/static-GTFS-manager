import os
from utils.logmessage import logmessage
from settings import uploadFolder

def uploadaFile(fileholder):
    # adapted from https://techoverflow.net/2015/06/09/upload-multiple-files-to-the-tornado-webserver/
    # receiving a form file object as argument.
    # saving to uploadFolder. In case same name file already exists, over-writing.

    filename = fileholder['filename'].replace("/", "")
    # zapping folder redirections if any

    logmessage('Saving filename: ' + filename + ' to ' + uploadFolder)

    if not os.path.exists(uploadFolder):
        os.makedirs(uploadFolder)

    with open(uploadFolder+filename, "wb") as out:
        # Be aware, that the user may have uploaded something evil like an executable script ...
        # so it is a good idea to check the file content (xfile['body']) before saving the file
        out.write(fileholder['body'])
    return filename