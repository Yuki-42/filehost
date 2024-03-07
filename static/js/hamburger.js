/*
    Code attributed to InactiveGaming13 on GitHub
 */

document.addEventListener("DOMContentLoaded", () => {
    const hamburger = document.querySelector(".hamburger");
    const navbarMenu = document.querySelector(".navbar-menu");
    hamburger.addEventListener("click", () => {
        hamburger.classList.toggle("active");
        navbarMenu.classList.toggle("active");
    });
});