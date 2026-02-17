async function toggleCandle(iconId) {
    const response = await fetch(`/icon/${iconId}/venerate`, { method: 'POST' });
    if (response.ok) {
        const data = await response.json();
        const btn = document.getElementById('candle-button');
        const count = document.getElementById('veneration-count');
        
        count.innerText = data.count;
        if (data.action === 'lit') {
            btn.classList.add('candle-active');
        } else {
            btn.classList.remove('candle-active');
        }
    }
}

const commentArea = document.getElementById('comment-text');
const charCount = document.getElementById('char-count');
const maxLength = 1000;

commentArea.addEventListener('input', () => {
    const remaining = maxLength - commentArea.value.length;
    charCount.innerText = remaining;

    // Optional: Turn the text red when they get close to the limit
    if (remaining < 50) {
        charCount.style.color = "#dc3545";
    } else {
        charCount.style.color = "inherit";
    }
});