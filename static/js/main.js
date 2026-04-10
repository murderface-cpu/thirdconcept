const POLL_INTERVAL = 30000; // 30 seconds

// Poll API for live settings and dynamically update content
async function fetchLiveData() {
    try {
        const response = await fetch("/api/live/settings");
        const data = await response.json();

        // Update logo and footer site name
        if (data.site_name) {
            document.querySelectorAll('.logo, .footer-section h3').forEach(el => {
                if (el.innerText.includes("Third Concept")) {
                    el.innerText = data.site_name;
                }
            });
        }

        // Update contact info in footer
        if (data.contact_email) {
            document.querySelectorAll('.footer-section').forEach(section => {
                if (section.innerHTML.includes("@")) {
                    section.innerHTML = `
                        <h3>Contact Info</h3>
                        <p>${data.address}</p>
                        <p>${data.contact_email}</p>
                        <p>${data.phone}</p>
                    `;
                }
            });
        }

        // Update contact info
        if (window.location.pathname.includes("/contact") && data.contact_email) {
            document.querySelectorAll('.card').forEach(section => {
                if (section.innerHTML.includes("📱")) {
                    section.innerHTML = `
                    <div class="card-icon">📱</div>
                    <h3>Call Us</h3>
                    <p>${data.phone}<br>
                    Available Monday - Friday, 8AM - 6PM EAT</p>
                    `;
                }
            });
        }

        // Update team page team list
        if (window.location.pathname.includes("/team") && data.team) {
            const container = document.querySelector(".team-grid");
            if (container) {
                container.innerHTML = data.team.map(member => `
                    <div class="team-card">
                        <div class="team-avatar">${member.avatar || getInitials(member.name)}</div>
                        <h3 class="team-name">${member.name}</h3>
                        <p class="team-role">${member.role}</p>
                        <p class="team-bio">${member.bio}</p>
                    </div>
                `).join('');
            }
        }

        // Update projects page projects list
if (window.location.pathname.includes("/activities") && data.projects) {
    const container = document.querySelector(".card-grid");
    if (container) {
        container.innerHTML = data.projects.map(project => `
            <div class="project-card" onclick="navigateToProject('${project.id || project.slug || project.title.toLowerCase().replace(/\s+/g, '-')}')" style="cursor: pointer;">
                <div class="project-image">${project.icon || '📁'}</div>
                <div class="project-info">
                    <h3 class="project-title">${project.title}</h3>
                    <p class="project-description">${project.description}</p>
                    <div class="project-tags">
                        ${(project.tags || '').split(',').map(tag => `<span class="tag">${tag.trim()}</span>`).join('')}
                    </div>
                </div>
            </div>
        `).join('');
    }
}



    } catch (err) {
        console.error("Polling error:", err);
    }
}

// Get initials for team avatars
function getInitials(name) {
    return name ? name.match(/\b\w/g).join('').toUpperCase() : '';
}

// Toggle mobile menu visibility
function toggleMobileMenu() {
    const menu = document.getElementById("mobileMenu");
    menu.style.display = (menu.style.display === "block") ? "none" : "block";
}

// Run polling on load and at intervals
window.addEventListener("DOMContentLoaded", fetchLiveData);
setInterval(fetchLiveData, POLL_INTERVAL);

// Function to handle project navigation
function navigateToProject(identifier) {
    // paused here for now
  window.location.href = `/projects/${identifier}`;
}

document.addEventListener('DOMContentLoaded', function () {
    // Configure marked for better rendering
    marked.setOptions({
        breaks: true,
        gfm: true,
        headerIds: false,
        mangle: false
    });

    const markdownContainer = document.getElementById('markdown-content');
    const markdownRaw = markdownContainer.querySelector('.markdown-raw');

    if (markdownRaw && markdownRaw.textContent.trim()) {
        // Get the raw markdown content
        const markdownText = markdownRaw.textContent.trim();

        // Render the markdown
        const renderedHtml = marked.parse(markdownText);

        // Replace the container content with rendered HTML
        markdownContainer.innerHTML = renderedHtml;
    }
});