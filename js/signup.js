// signup.js - the brain for signup.html
// checks the two passwords match, creates the account on our backend,
// then sends the user to the login page

const form = document.getElementById("signupForm");
const errorBox = document.getElementById("formError");

form.addEventListener("submit", async (e) => {
    e.preventDefault(); // stop the page from reloading

    const password = document.getElementById("password").value;
    const confirm = document.getElementById("confirm").value;

    if (password !== confirm) {
        errorBox.textContent = "Passwords don't match.";
        errorBox.hidden = false;
        return;
    }

    try {
        const res = await fetch("http://localhost:8000/signup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                username: document.getElementById("email").value,
                password: password,
            }),
        });
        const data = await res.json();

        if (data.status === "account created") {
            window.location.href = "login.html"; // account made - go log in
        } else {
            errorBox.textContent = data.error; // ex: username already taken
            errorBox.hidden = false;
        }
    } catch (err) {
        errorBox.textContent = "Can't reach the server - is the backend running?";
        errorBox.hidden = false;
    }
});

// Show/Hide password buttons
document.querySelectorAll("[data-toggle-password]").forEach((btn) => {
    btn.addEventListener("click", () => {
        const input = document.getElementById(btn.dataset.togglePassword);
        input.type = input.type === "password" ? "text" : "password";
        btn.textContent = input.type === "password" ? "Show" : "Hide";
    });
});