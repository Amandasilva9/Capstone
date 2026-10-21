// login.js - the brain for login.html
// stops the form from reloading the page, sends the login to our backend,
// and moves the user to the dashboard if the password checks out

const form = document.getElementById("loginForm");
const errorBox = document.getElementById("formError");

form.addEventListener("submit", async (e) => {
    e.preventDefault(); // stop the browser's default "reload the page" behavior

    try {
        const res = await fetch("http://localhost:8000/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                username: document.getElementById("email").value,
                password: document.getElementById("password").value,
            }),
        });
        const data = await res.json();

        if (data.status === "logged in") {
            // remember who's logged in so other pages can greet them
            localStorage.setItem("username", document.getElementById("email").value);
            window.location.href = "dashboard.html"; // the "next page" part
        } else {
            errorBox.textContent = data.error; // wrong username/password
            errorBox.hidden = false;
        }
    } catch (err) {
        errorBox.textContent = "Can't reach the server - is the backend running?";
        errorBox.hidden = false;
    }
});

// the little Show/Hide button on the password box
document.querySelectorAll("[data-toggle-password]").forEach((btn) => {
    btn.addEventListener("click", () => {
        const input = document.getElementById(btn.dataset.togglePassword);
        input.type = input.type === "password" ? "text" : "password";
        btn.textContent = input.type === "password" ? "Show" : "Hide";
    });
});