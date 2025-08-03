const container = document.getElementById("container");
const registerBtn = document.getElementById("register");
const loginBtn = document.getElementById("login");

registerBtn.addEventListener("click", () => {
  container.classList.add("active");
});

loginBtn.addEventListener("click", () => {
  container.classList.remove("active");
});

document.addEventListener('DOMContentLoaded', function() {
  const flashMessage = document.querySelector('.alert');
  if (flashMessage) {
      setTimeout(function() {
          flashMessage.classList.add('fade-out');
          setTimeout(function() {
              flashMessage.remove();
          }, 500);
      }, 3000);
  }
});