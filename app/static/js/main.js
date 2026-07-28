function goTo(path) {
    window.location.href = path;
}

function updateBadgeState(badge, count) {
    if (!badge) return;
    badge.textContent = count;
    badge.style.display = count > 0 ? 'inline-flex' : 'none';
}

async function updateCartCount() {
    const badges = document.querySelectorAll('#cart-count-badge, #cart-count');
    if (!badges.length) return;

    try {
        const response = await fetch('/cart/', {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            badges.forEach((badge) => updateBadgeState(badge, '0'));
            return;
        }

        const items = await response.json();
        const count = Array.isArray(items)
            ? items.reduce((sum, item) => sum + (Number(item?.quantity) || 0), 0)
            : 0;

        badges.forEach((badge) => updateBadgeState(badge, count));
    } catch (error) {
        badges.forEach((badge) => updateBadgeState(badge, '0'));
    }
}

window.goTo = goTo;
window.updateCartCount = updateCartCount;
