/**
 * static/js/recommendations.js
 *
 * Fetches "you may also like" recommendations for the current product
 * and renders them into #recommendations-container.
 *
 * USAGE: called from product_detail.html as loadRecommendations(product.id)
 */

async function loadRecommendations(productId, topN = 6) {
  const container = document.getElementById("recommendations-container");
  if (!container) {
    console.error("recommendations.js: #recommendations-container not found on page.");
    return;
  }

  container.innerHTML = `<p class="text-on-surface-variant">Loading recommendations...</p>`;

  try {
    const response = await fetch(`/products/${productId}/similar?top_n=${topN}`);

    if (!response.ok) {
      // 404 = product not found, 503 = model not trained yet
      container.innerHTML = "";
      return;
    }

    const data = await response.json();
    renderRecommendations(container, data.recommendations);
  } catch (err) {
    console.error("Failed to load recommendations:", err);
    container.innerHTML = "";
  }
}

function renderRecommendations(container, recommendations) {
  if (!recommendations || recommendations.length === 0) {
    container.innerHTML = "";
    return;
  }

  const imageFallback = 'https://images.unsplash.com/photo-1445205170230-053b83016050?auto=format&fit=crop&w=900&q=85';
  const cardsHtml = recommendations
    .map(
      (item) => `
      <article class="rec-card group">
        <a href="/product/${item.id}" aria-label="View ${escapeHtml(item.name || 'product')}">
        <div class="rec-card-img-container aspect-square bg-surface-container-low mb-4">
          <img alt="${escapeHtml(item.name || "")}" class="w-full h-full object-cover"
               src="${item.image || imageFallback}" onerror="this.onerror=null;this.src='${imageFallback}'"/>
        </div>
        <p class="font-label-lg text-label-lg uppercase tracking-tight text-primary">${escapeHtml(item.name || "")}</p>
        <p class="text-body-md text-on-surface-variant">${escapeHtml(item.category || "")}</p>
        <p class="font-bold text-primary mt-1">${formatINR(item.price)}</p>
        </a>
        <button type="button" class="recommendation-add-to-cart-btn mt-3 w-full border border-primary py-2 text-sm uppercase tracking-widest hover:bg-primary hover:text-white" data-product-id="${item.id}">Add to Cart</button>
      </article>
    `
    )
    .join("");

  container.innerHTML = `
    <div class="border-t border-outline-variant pt-stack-md mt-stack-lg">
      <h2 class="font-display-lg text-headline-md text-primary mb-8">You may also like</h2>
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-gutter gap-y-8">${cardsHtml}</div>
    </div>
  `;

  container.querySelectorAll('.recommendation-add-to-cart-btn').forEach((button) => {
    button.addEventListener('click', async () => {
      button.disabled = true;
      try {
        await addToCart({ product_id: Number(button.dataset.productId), quantity: 1 });
        button.textContent = 'Added';
        if (typeof refreshCartCount === 'function') await refreshCartCount();
        setTimeout(() => {
          button.textContent = 'Add to Cart';
          button.disabled = false;
        }, 1500);
      } catch (err) {
        alert(err.message || 'Could not add this product to the cart.');
        button.disabled = false;
      }
    });
  });
}

// Basic HTML-escaping so product names can't break the markup
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
