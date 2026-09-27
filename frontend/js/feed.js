/* Shared post-card rendering + interaction wiring, used by home.html and tea.html. */

function postCardHtml(post) {
  const authorInitial = initials(post.author.display_name);
  const media = post.media_urls.map(u => `<img src="${API_BASE}${u}" style="width:100%;border-radius:12px;margin-top:8px;">`).join("");
  let pollHtml = "";
  if (post.poll) {
    const total = post.poll.total_votes || 0;
    pollHtml = `<div style="margin-top:10px;">` + post.poll.options.map(o => {
      const pct = total ? Math.round((o.votes / total) * 100) : 0;
      const voted = post.poll.user_voted_option_id === o.id;
      return `<div class="poll-option" data-option="${o.id}" data-poll-done="${post.poll.user_voted_option_id ? '1' : '0'}">
        <div class="fill" style="width:${pct}%;"></div>
        <div class="label"><span>${voted ? "✓ " : ""}${escapeHtml(o.text)}</span><span>${pct}% (${o.votes})</span></div>
      </div>`;
    }).join("") + `</div>`;
  }
  return `
  <div class="card post-card fade-in" data-post-id="${post.id}">
    <div class="post-header">
      <div class="avatar">${authorInitial}</div>
      <div class="post-meta">
        <span class="post-author">${escapeHtml(post.author.display_name)}</span>
        <span class="post-time">${timeAgo(post.created_at)} ${post.category ? `· <span class="category-badge">${post.category}</span>` : ""}</span>
      </div>
    </div>
    <div class="post-text">${post.text}</div>
    ${media}
    ${pollHtml}
    <div class="post-actions">
      <button class="action-btn react-btn">❤️ ${post.reaction_count}</button>
      <button class="action-btn comment-toggle">💬 ${post.comment_count}</button>
      <button class="action-btn report-btn">🚩 Report</button>
    </div>
    <div class="comments-box" style="display:none; margin-top:10px; border-top:1px solid var(--border); padding-top:10px;">
      <div class="comments-list"></div>
      <div style="display:flex; gap:8px; margin-top:8px;">
        <input type="text" class="comment-input" placeholder="Write a comment...">
        <button class="btn btn-secondary btn-sm comment-send">Send</button>
      </div>
    </div>
  </div>`;
}

function wireCardEvents(container) {
  container.querySelectorAll(".post-card").forEach(card => {
    if (card.dataset.wired) return;
    card.dataset.wired = "1";
    const postId = card.dataset.postId;

    card.querySelector(".react-btn").addEventListener("click", async (e) => {
      const res = await api("/api/posts/reactions", { method: "POST", body: { target_type: "post", target_id: parseInt(postId) } });
      const btn = e.currentTarget;
      let count = parseInt(btn.textContent.trim().split(" ")[1]);
      count += res.reacted ? 1 : -1;
      btn.textContent = `❤️ ${count}`;
      btn.classList.toggle("active", res.reacted);
    });

    card.querySelector(".comment-toggle").addEventListener("click", async () => {
      const box = card.querySelector(".comments-box");
      const willShow = box.style.display === "none";
      box.style.display = willShow ? "block" : "none";
      if (willShow) {
        const comments = await api(`/api/posts/${postId}/comments`);
        card.querySelector(".comments-list").innerHTML = comments.map(c =>
          `<div style="margin-bottom:6px; font-size:0.85rem;"><b>${escapeHtml(c.author.display_name)}:</b> ${c.text}</div>`
        ).join("") || `<div style="color:var(--text-faint); font-size:0.85rem;">No comments yet.</div>`;
      }
    });

    card.querySelector(".comment-send").addEventListener("click", async () => {
      const input = card.querySelector(".comment-input");
      const text = input.value.trim();
      if (!text) return;
      await api(`/api/posts/${postId}/comments`, { method: "POST", body: { text } });
      input.value = "";
      card.querySelector(".comment-toggle").click();
      card.querySelector(".comment-toggle").click();
    });

    card.querySelector(".report-btn").addEventListener("click", async () => {
      const reason = prompt("Reason for reporting (spam, harassment, nudity, hate_speech, other):", "spam");
      if (!reason) return;
      await api("/api/moderation/reports", { method: "POST", body: { target_type: "post", target_id: parseInt(postId), reason } });
      showToast("Report submitted. Thank you.");
    });

    card.querySelectorAll(".poll-option").forEach(opt => {
      opt.addEventListener("click", async () => {
        if (opt.dataset.pollDone === "1") return showToast("You already voted in this poll.");
        try {
          await api(`/api/posts/polls/${opt.dataset.option}/vote`, { method: "POST" });
          if (window.reloadFeedCallback) window.reloadFeedCallback();
        } catch (err) { showToast(err.message); }
      });
    });
  });
}
