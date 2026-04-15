// Main JavaScript file for InstaClone

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    initializeComponents();
    setupEventListeners();
});

// Initialize Components
function initializeComponents() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Initialize image modals
    initImageModals();
    
    // Initialize infinite scroll
    initInfiniteScroll();
    
    // Initialize file upload previews
    initFileUploadPreviews();
    
    // Initialize real-time updates
    initRealTimeUpdates();
}

// Setup Event Listeners
function setupEventListeners() {
    // Like buttons
    document.querySelectorAll('.like-btn').forEach(button => {
        button.addEventListener('click', handleLike);
    });

    // Follow buttons
    document.querySelectorAll('.follow-btn').forEach(button => {
        button.addEventListener('click', handleFollow);
    });

    // Comment forms
    document.querySelectorAll('.comment-form').forEach(form => {
        form.addEventListener('submit', handleCommentSubmit);
    });

    // Save post buttons
    document.querySelectorAll('.save-btn').forEach(button => {
        button.addEventListener('click', handleSavePost);
    });

    // Share buttons
    document.querySelectorAll('.share-btn').forEach(button => {
        button.addEventListener('click', handleShare);
    });

    // Story creation
    const storyCreateBtn = document.getElementById('create-story-btn');
    if (storyCreateBtn) {
        storyCreateBtn.addEventListener('click', handleCreateStory);
    }

    // Search functionality
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', handleSearch);
    }

    // File upload
    const fileUploadInputs = document.querySelectorAll('input[type="file"]');
    fileUploadInputs.forEach(input => {
        input.addEventListener('change', handleFileUpload);
    });

    // Message sending
    const messageForm = document.getElementById('message-form');
    if (messageForm) {
        messageForm.addEventListener('submit', handleMessageSend);
    }

    // Notification read
    const notificationItems = document.querySelectorAll('.notification-item');
    notificationItems.forEach(item => {
        item.addEventListener('click', markNotificationAsRead);
    });
}

// Like Handler
async function handleLike(event) {
    event.preventDefault();
    const button = event.currentTarget;
    const postId = button.dataset.postId;
    const reelId = button.dataset.reelId;
    
    if (!postId && !reelId) return;
    
    const url = postId ? `/like_post/${postId}` : `/like_reel/${reelId}`;
    
    try {
        button.disabled = true;
        button.classList.add('pulse');
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin'
        });
        
        const data = await response.json();
        
        if (data.status) {
            // Update like button
            const icon = button.querySelector('i');
            if (data.status === 'liked') {
                icon.classList.remove('far');
                icon.classList.add('fas', 'text-danger');
                button.classList.add('liked');
            } else {
                icon.classList.remove('fas', 'text-danger');
                icon.classList.add('far');
                button.classList.remove('liked');
            }
            
            // Update like count
            const likeCountElement = button.querySelector('.like-count') || 
                                   document.getElementById(`like-count-${postId || reelId}`);
            if (likeCountElement) {
                likeCountElement.textContent = data.count;
            }
        }
    } catch (error) {
        console.error('Error liking:', error);
        showToast('Failed to like. Please try again.', 'error');
    } finally {
        button.disabled = false;
        button.classList.remove('pulse');
    }
}

// Follow Handler
async function handleFollow(event) {
    event.preventDefault();
    const button = event.currentTarget;
    const username = button.dataset.username;
    
    if (!username) return;
    
    try {
        button.disabled = true;
        
        const response = await fetch(`/follow/${username}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin'
        });
        
        const data = await response.json();
        
        if (!data.error) {
            // Update follow button
            if (data.following) {
                button.textContent = 'Following';
                button.classList.remove('btn-primary');
                button.classList.add('btn-outline-primary');
            } else {
                button.textContent = 'Follow';
                button.classList.remove('btn-outline-primary');
                button.classList.add('btn-primary');
            }
            
            // Update follower count
            const followerCountElement = document.getElementById('follower-count');
            if (followerCountElement) {
                followerCountElement.textContent = data.followers_count;
            }
            
            showToast(data.following ? 'Followed successfully!' : 'Unfollowed successfully!', 'success');
        } else {
            showToast(data.error, 'error');
        }
    } catch (error) {
        console.error('Error following:', error);
        showToast('Failed to follow. Please try again.', 'error');
    } finally {
        button.disabled = false;
    }
}

// Comment Handler
async function handleCommentSubmit(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const postId = form.dataset.postId;
    const reelId = form.dataset.reelId;
    const input = form.querySelector('input[type="text"], textarea');
    const content = input.value.trim();
    
    if (!content) return;
    
    if (!postId && !reelId) return;
    
    const url = postId ? `/comment_post/${postId}` : `/comment_reel/${reelId}`;
    
    try {
        // Disable form
        const submitButton = form.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCSRFToken()
            },
            body: `content=${encodeURIComponent(content)}`,
            credentials: 'same-origin'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Clear input
            input.value = '';
            
            // Add comment to UI
            addCommentToUI(data.comment, postId || reelId);
            
            // Update comment count
            updateCommentCount(postId || reelId, true);
        } else {
            showToast('Failed to post comment. Please try again.', 'error');
        }
    } catch (error) {
        console.error('Error posting comment:', error);
        showToast('Failed to post comment. Please try again.', 'error');
    } finally {
        const submitButton = form.querySelector('button[type="submit"]');
        submitButton.disabled = false;
    }
}

// Save Post Handler
async function handleSavePost(event) {
    event.preventDefault();
    const button = event.currentTarget;
    const postId = button.dataset.postId;
    
    if (!postId) return;
    
    try {
        button.disabled = true;
        
        const response = await fetch(`/save_post/${postId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin'
        });
        
        const data = await response.json();
        
        if (data.saved !== undefined) {
            // Update save button
            const icon = button.querySelector('i');
            if (data.saved) {
                icon.classList.remove('far');
                icon.classList.add('fas', 'text-warning');
                button.classList.add('saved');
                showToast('Post saved!', 'success');
            } else {
                icon.classList.remove('fas', 'text-warning');
                icon.classList.add('far');
                button.classList.remove('saved');
                showToast('Post removed from saved!', 'info');
            }
        }
    } catch (error) {
        console.error('Error saving post:', error);
        showToast('Failed to save post. Please try again.', 'error');
    } finally {
        button.disabled = false;
    }
}

// Share Handler
async function handleShare(event) {
    event.preventDefault();
    const button = event.currentTarget;
    const postId = button.dataset.postId;
    const reelId = button.dataset.reelId;
    
    if (!postId && !reelId) return;
    
    try {
        const url = postId ? `/share_post/${postId}` : `/share_reel/${reelId}`;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            credentials: 'same-origin'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Copy to clipboard if Web Share API is not available
            if (navigator.share) {
                try {
                    await navigator.share({
                        title: 'Check out this post on InstaClone!',
                        url: data.share_url
                    });
                } catch (shareError) {
                    // Fallback to clipboard
                    await copyToClipboard(data.share_url);
                    showToast('Link copied to clipboard!', 'success');
                }
            } else {
                await copyToClipboard(data.share_url);
                showToast('Link copied to clipboard!', 'success');
            }
        }
    } catch (error) {
        console.error('Error sharing:', error);
        showToast('Failed to share. Please try again.', 'error');
    }
}

// Search Handler
async function handleSearch(event) {
    const input = event.target;
    const query = input.value.trim();
    
    if (query.length < 2) {
        hideSearchResults();
        return;
    }
    
    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        displaySearchResults(data);
    } catch (error) {
        console.error('Error searching:', error);
    }
}

// Create Story Handler
async function handleCreateStory() {
    // Create file input for story upload
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.style.display = 'none';
    
    input.addEventListener('change', async function() {
        if (this.files && this.files[0]) {
            const formData = new FormData();
            formData.append('image', this.files[0]);
            
            try {
                const response = await fetch('/create_story', {
                    method: 'POST',
                    body: formData,
                    credentials: 'same-origin'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showToast('Story created successfully!', 'success');
                    // Reload stories after a short delay
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    showToast('Failed to create story. Please try again.', 'error');
                }
            } catch (error) {
                console.error('Error creating story:', error);
                showToast('Failed to create story. Please try again.', 'error');
            }
        }
    });
    
    document.body.appendChild(input);
    input.click();
    document.body.removeChild(input);
}

// Message Send Handler
async function handleMessageSend(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const input = form.querySelector('input[type="text"], textarea');
    const content = input.value.trim();
    const receiverId = form.dataset.receiverId;
    
    if (!content || !receiverId) return;
    
    try {
        const response = await fetch('/api/send_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                receiver_id: receiverId,
                content: content
            }),
            credentials: 'same-origin'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Clear input
            input.value = '';
            
            // Add message to UI
            addMessageToUI(content, true);
            
            // Scroll to bottom
            scrollChatToBottom();
        } else {
            showToast('Failed to send message. Please try again.', 'error');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        showToast('Failed to send message. Please try again.', 'error');
    }
}

// Helper Functions
function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.getAttribute('content') : '';
}

function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    // Add to container
    const container = document.getElementById('toast-container') || createToastContainer();
    container.appendChild(toast);
    
    // Initialize and show
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove after hide
    toast.addEventListener('hidden.bs.toast', function () {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1060';
    document.body.appendChild(container);
    return container;
}

async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (error) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        return true;
    }
}

function addCommentToUI(comment, targetId) {
    const commentsContainer = document.querySelector(`#comments-${targetId}`) ||
                            document.querySelector('.comments-section');
    
    if (commentsContainer) {
        const commentElement = document.createElement('div');
        commentElement.className = 'comment-item fade-in';
        commentElement.innerHTML = `
            <div class="comment-author">
                <img src="/static/uploads/profiles/${comment.profile_pic}" 
                     alt="${comment.username}" 
                     class="comment-avatar">
                <div>
                    <span class="comment-username">${comment.username}</span>
                    <small class="comment-time">${comment.created_at}</small>
                </div>
            </div>
            <div class="comment-content">${comment.content}</div>
        `;
        
        commentsContainer.appendChild(commentElement);
        commentsContainer.scrollTop = commentsContainer.scrollHeight;
    }
}

function updateCommentCount(targetId, increment = true) {
    const countElement = document.querySelector(`#comment-count-${targetId}`) ||
                        document.querySelector('.comment-count');
    
    if (countElement) {
        const currentCount = parseInt(countElement.textContent) || 0;
        countElement.textContent = increment ? currentCount + 1 : currentCount - 1;
    }
}

function addMessageToUI(content, isOwn = false) {
    const messagesContainer = document.querySelector('.chat-messages');
    
    if (messagesContainer) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${isOwn ? 'sent' : 'received'}`;
        
        const now = new Date();
        const timeString = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageElement.innerHTML = `
            <div class="message-bubble">
                ${content}
                <span class="message-time">${timeString}</span>
            </div>
        `;
        
        messagesContainer.appendChild(messageElement);
        scrollChatToBottom();
    }
}

function scrollChatToBottom() {
    const messagesContainer = document.querySelector('.chat-messages');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

function displaySearchResults(data) {
    const resultsContainer = document.getElementById('search-results');
    if (!resultsContainer) return;
    
    resultsContainer.innerHTML = '';
    
    if (data.users && data.users.length > 0) {
        const usersSection = document.createElement('div');
        usersSection.className = 'search-section';
        
        data.users.forEach(user => {
            const userElement = document.createElement('a');
            userElement.href = `/profile/${user.username}`;
            userElement.className = 'search-result-item';
            userElement.innerHTML = `
                <img src="/static/uploads/profiles/${user.profile_pic}" 
                     alt="${user.username}" 
                     class="search-result-avatar">
                <div class="search-result-info">
                    <div class="search-result-username">${user.username}</div>
                    ${user.is_following ? '<small class="text-muted">Following</small>' : ''}
                </div>
            `;
            usersSection.appendChild(userElement);
        });
        
        resultsContainer.appendChild(usersSection);
        resultsContainer.style.display = 'block';
    } else {
        resultsContainer.innerHTML = '<div class="text-center p-4 text-muted">No results found</div>';
        resultsContainer.style.display = 'block';
    }
}

function hideSearchResults() {
    const resultsContainer = document.getElementById('search-results');
    if (resultsContainer) {
        resultsContainer.style.display = 'none';
    }
}

function initImageModals() {
    // Add click handlers to images for modal view
    document.querySelectorAll('.post-image, .explore-item img').forEach(img => {
        img.addEventListener('click', function() {
            const modal = new bootstrap.Modal(document.getElementById('imageModal'));
            const modalImage = document.getElementById('modalImage');
            modalImage.src = this.src;
            modalImage.alt = this.alt;
            modal.show();
        });
    });
}

function initInfiniteScroll() {
    let isLoading = false;
    let page = 1;
    const hasNextPage = document.body.dataset.hasNextPage === 'true';
    
    if (!hasNextPage) return;
    
    window.addEventListener('scroll', async function() {
        if (isLoading) return;
        
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollHeight = document.documentElement.scrollHeight;
        const clientHeight = document.documentElement.clientHeight;
        
        if (scrollTop + clientHeight >= scrollHeight - 100) {
            isLoading = true;
            page++;
            
            try {
                const url = window.location.pathname + `?page=${page}`;
                const response = await fetch(url);
                const data = await response.text();
                
                // Parse HTML and extract posts
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = data;
                const posts = tempDiv.querySelectorAll('.post');
                
                if (posts.length > 0) {
                    const container = document.querySelector('.posts-container') || 
                                    document.querySelector('.feed');
                    posts.forEach(post => {
                        container.appendChild(post);
                    });
                } else {
                    // No more posts
                    window.removeEventListener('scroll', arguments.callee);
                }
            } catch (error) {
                console.error('Error loading more posts:', error);
            } finally {
                isLoading = false;
            }
        }
    });
}

function initFileUploadPreviews() {
    document.querySelectorAll('input[type="file"][data-preview]').forEach(input => {
        input.addEventListener('change', function() {
            const previewId = this.dataset.preview;
            const preview = document.getElementById(previewId);
            
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    if (preview) {
                        preview.src = e.target.result;
                        preview.style.display = 'block';
                    }
                }
                
                reader.readAsDataURL(this.files[0]);
            }
        });
    });
}

function initRealTimeUpdates() {
    // Initialize WebSocket for real-time updates if available
    if ('WebSocket' in window) {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws`;
        
        try {
            const socket = new WebSocket(wsUrl);
            
            socket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleRealTimeUpdate(data);
            };
            
            socket.onclose = function() {
                // Try to reconnect after 5 seconds
                setTimeout(initRealTimeUpdates, 5000);
            };
        } catch (error) {
            console.error('WebSocket connection failed:', error);
        }
    }
}

function handleRealTimeUpdate(data) {
    switch (data.type) {
        case 'like':
            updateLikeCount(data.post_id, data.count);
            break;
        case 'comment':
            addCommentToUI(data.comment, data.post_id);
            break;
        case 'message':
            if (data.receiver_id === currentUserId) {
                addMessageToUI(data.content, false);
                showNotification('New message', `You have a new message from ${data.sender}`);
            }
            break;
        case 'follow':
            if (data.followed_id === currentUserId) {
                showNotification('New follower', `${data.follower} started following you!`);
            }
            break;
    }
}

function updateLikeCount(postId, count) {
    const likeCountElement = document.getElementById(`like-count-${postId}`);
    if (likeCountElement) {
        likeCountElement.textContent = count;
    }
}

function showNotification(title, body) {
    // Check if notifications are supported and granted
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, { body: body, icon: '/static/favicon.ico' });
    }
}

// Export for use in other scripts
window.InstaClone = {
    handleLike,
    handleFollow,
    handleCommentSubmit,
    handleSavePost,
    handleShare,
    showToast,
    copyToClipboard
};