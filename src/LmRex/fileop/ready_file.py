"""Module containing file functions"""

import glob
import os
import requests

SHP_EXT = 'shp'
SHP_EXTENSIONS = [
    '.shp', '.shx', '.dbf', '.prj', '.sbn', '.sbx', '.fbn', '.fbx', '.ain', 
    '.aih', '.ixs', '.mxs', '.atx', '.shp.xml', '.cpg', '.qix'],


# ...............................................
def ready_filename(full_filename, overwrite=False):
    """Prepare the specified file location for writing."""
    if full_filename is None:
        raise Exception('Full filename is None')

    if os.path.exists(full_filename):
        if overwrite:
            success, msg = delete_file(full_filename)
            if not success:
                raise Exception('Unable to delete {}: {}'.format(
                    full_filename, msg))

            return True

        return False

    pth, _ = os.path.split(full_filename)
    try:
        os.makedirs(pth, 0o775)
    except OSError:
        pass

    if os.path.isdir(pth):
        return True

    raise Exception(
        'Failed to create dirs {}, checking for ready_filename {}'.format(
            pth, full_filename))


# ...............................................
def delete_file(file_name, delete_dir=False):
    """Delete file if it exists, delete directory if it becomes empty

    Note:
        If file is shapefile, delete all related files
    """
    success = True
    msg = ''
    if file_name is None:
        msg = 'Cannot delete file \'None\''
    else:
        pth, _ = os.path.split(file_name)
        if file_name is not None and os.path.exists(file_name):
            base, ext = os.path.splitext(file_name)
            if ext == SHP_EXT:
                similar_file_names = glob.glob(base + '.*')
                try:
                    for sim_file_name in similar_file_names:
                        _, sim_ext = os.path.splitext(sim_file_name)
                        if sim_ext in SHP_EXTENSIONS:
                            os.remove(sim_file_name)
                except Exception as e:
                    success = False
                    msg = 'Failed to remove {}, {}'.format(
                        sim_file_name, str(e))
            else:
                try:
                    os.remove(file_name)
                except Exception as e:
                    success = False
                    msg = 'Failed to remove {}, {}'.format(file_name, str(e))
            if delete_dir and len(os.listdir(pth)) == 0:
                try:
                    os.removedirs(pth)
                except Exception as e:
                    success = False
                    msg = 'Failed to remove {}, {}'.format(pth, str(e))
    return success, msg


# .............................
# def zip_files(fnames, zip_fname):
#     """Returns a wrapper around a tar gzip file stream
# 
#     Args:
#         base_name: (optional) If provided, this will be the prefix for the
#             names of the shape file's files in the zip file.
#     """
#     tg_stream = StringIO()
#     zipf = zipfile.ZipFile(
#         tg_stream, mode='w', compression=zipfile.ZIP_DEFLATED,
#         allowZip64=True)
# 
#     for fname in fnames:
#         ext = os.path.splitext(fname)[1]
#         zipf.write(fname, '{}.{}'.format(zip_fname, ext))
#     zipf.close()
# 
#     tg_stream.seek(0)
#     ret = ''.join(tg_stream.readlines())
#     tg_stream.close()
#     return ret
