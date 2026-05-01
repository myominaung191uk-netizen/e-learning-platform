function toggleMenu() {
    const navLinks = document.getElementById("navLinks");
    navLinks.classList.toggle("show");
}

function confirmAction(message) {
    return confirm(message);
}

console.log("E-learning platform loaded successfully.");
