var dark = false;


document.getElementById("dark-mode").addEventListener("click", function () {
    console.log("clicked");
    dark = !dark;
    const container = document.getElementById("container");
    const contents = document.getElementsByClassName("content");
    const btn = document.getElementById("dark-mode");


    if (dark) {
        container.classList.remove("container-light");
        container.classList.add("container-dark");
        btn.innerHTML = "Light Mode";

        for (let i = 0; i < contents.length; i++) {
            contents[i].classList.add("content-dark");
            contents[i].classList.remove("content-light");

        }
    } else {
        container.classList.remove("container-dark");
        container.classList.add("container-light");
        btn.innerHTML = "Dark Mode";

        for (let i = 0; i < contents.length; i++) {
            contents[i].classList.add("content-light");
            contents[i].classList.remove("content-dark");

        }
    }
})