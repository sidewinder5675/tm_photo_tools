function createGif(projectPath) {
  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/create_gif", true);
  xhr.setRequestHeader("Content-Type", "application/json");

  xhr.onreadystatechange = function () {
    if (xhr.readyState === 4 && xhr.status === 200) {
      console.log("GIF creation successful!");
    }
  };

  xhr.send(JSON.stringify({ projectPath: projectPath }));
}
