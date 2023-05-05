function folder_exists(basePath, folderName) {
  var xhr = new XMLHttpRequest();
  xhr.open("HEAD", basePath + "/" + folderName, false);
  xhr.send();
  return xhr.status !== 404;
}
