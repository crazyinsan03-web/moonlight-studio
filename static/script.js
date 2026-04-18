// Sirf Search filter rakhenge Main Page par
function filterSongs() {
    let input = document.getElementById('searchInput').value.toLowerCase();
    let cards = document.getElementsByClassName('sp-card');

    for (let card of cards) {
        let title = card.querySelector('.sp-title').innerText.toLowerCase();
        if (title.includes(input)) {
            card.parentElement.style.display = "block"; // <a> tag ko dikhao
        } else {
            card.parentElement.style.display = "none";
        }
    }
}

// Baki saare openPlayer, togglePlay functions yahan se hata de 
// Kyunki woh ab player.html ke apne script mein honge.




function addToRecent(id, title, thumb) {
    let recent = JSON.parse(localStorage.getItem('moonlight_recent') || "[]");
    
    // Purana same gaana hatao
    recent = recent.filter(s => s.id !== id);
    
    // Naya gaana top par
    recent.unshift({ id, title, thumb });
    
    // Sirf 10 gaane yaad rakho
    if (recent.length > 10) recent.pop();
    
    localStorage.setItem('moonlight_recent', JSON.stringify(recent));
}
