// Form switch karne ke liye (Login <-> Signup)
function toggleForm() {
    const signup = document.getElementById('signup-form');
    const login = document.getElementById('login-form');
    if(signup.style.display === "none") {
        signup.style.display = "block";
        login.style.display = "none";
    } else {
        signup.style.display = "none";
        login.style.display = "block";
    }
}

// --- SIGNUP LOGIC (NEON DB CONNECTION) ---
async function handleSignup() {
    const name = document.getElementById('reg-name').value;
    const phone = document.getElementById('reg-phone').value;
    const pass = document.getElementById('reg-pass').value;

    if(!name || !phone || !pass) return alert("Bhai, saari details toh bhar!");

    try {
        const response = await fetch('/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                name: name, 
                phone: phone, 
                password: pass 
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            // Browser mein data tabhi save hoga jab DB mein save ho jayega
            localStorage.setItem('isLoggedIn', 'true');
            localStorage.setItem('moonlight_user_name', data.user_name);
            localStorage.setItem('user_phone', phone);
            
            alert("Account ban gaya! Welcome to Moonlight Studio 🌙");
            window.location.href = "/"; 
        } else {
            alert("Signup Failed: " + data.message);
        }
    } catch (error) {
        console.error("Error:", error);
        alert("Server connect nahi ho raha, app.py check kar!");
    }
}

// --- LOGIN LOGIC (NEON DB VERIFICATION) ---
async function handleLogin() {
    const phone = document.getElementById('login-phone').value;
    const pass = document.getElementById('login-pass').value;

    if(!phone || !pass) return alert("Phone aur Password toh daal bhai!");

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                phone: phone, 
                password: pass 
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            localStorage.setItem('isLoggedIn', 'true');
            localStorage.setItem('moonlight_user_name', data.user_name);
            localStorage.setItem('user_phone', phone);
            
            window.location.href = "/"; 
        } else {
            alert("Galti hai bhai: " + data.message);
        }
    } catch (error) {
        console.error("Error:", error);
        alert("Backend se response nahi aaya!");
    }
}
