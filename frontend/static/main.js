window.onload = function() {
    var savedBaseUrl = localStorage.getItem('apiBaseUrl');
    if (savedBaseUrl) {
        document.getElementById('api-base-url').value = savedBaseUrl;
        loadPosts();
    }
}

function loadPosts() {
    var baseUrl = document.getElementById('api-base-url').value;
    localStorage.setItem('apiBaseUrl', baseUrl);

    fetch(baseUrl + '/posts')
        .then(response => response.json())
        .then(data => {
            console.log('Fetched data:', data); 

            const posts = data.posts;

            if (Array.isArray(posts)) {
                const postContainer = document.getElementById('post-container');
                postContainer.innerHTML = '';

                posts.forEach(post => {
                    const postDiv = document.createElement('div');
                    postDiv.className = 'post';
                    postDiv.innerHTML = `
                        <h2>${post.title}</h2>
                        <p><strong>Author:</strong> ${post.author}</p>
                        <p><strong>Date:</strong> ${post.date}</p>
                        <p>${post.content}</p>
                        <p><strong>Likes:</strong> ${post.likes || 0}</p>
                        <button onclick="likePost(${post.id})">Like</button>
                        <button onclick="deletePost(${post.id})">Delete</button>
                        <div>
                            <h3>Comments:</h3>
                            <ul>
                                ${post.comments.map(comment => `<li>${comment}</li>`).join('')}
                            </ul>
                            <input type="text" id="comment-${post.id}" placeholder="Add a comment">
                            <button onclick="addComment(${post.id})">Add Comment</button>
                        </div>
                    `;
                    postContainer.appendChild(postDiv);
                });
            } else {
                console.error('Expected an array but got:', posts);
            }
        })
        .catch(error => console.error('Error:', error));
}


function addPost() {
    var baseUrl = document.getElementById('api-base-url').value;
    var postTitle = document.getElementById('post-title').value;
    var postAuthor = document.getElementById('post-author').value;
    var postDate = document.getElementById('post-date').value;
    var postContent = document.getElementById('post-content').value;

    fetch(baseUrl + '/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: postTitle, author: postAuthor, date: postDate, content: postContent })
    })
    .then(response => response.json())
    .then(post => {
        console.log('Post added:', post);
        loadPosts();
    })
    .catch(error => console.error('Error:', error));
}

function searchAndSortPosts() {
    var baseUrl = document.getElementById('api-base-url').value;
    var query = document.getElementById('search-query').value;
    var sortField = document.getElementById('sort-field').value;
    var sortDirection = document.getElementById('sort-direction').value;

    fetch(`${baseUrl}/posts/search?title=${encodeURIComponent(query)}&sort=${sortField}&direction=${sortDirection}`)
        .then(response => response.json())
        .then(data => {
            const postContainer = document.getElementById('post-container');
            postContainer.innerHTML = '';

            data.forEach(post => {
                const postDiv = document.createElement('div');
                postDiv.className = 'post';
                postDiv.innerHTML = `
                    <h2>${post.title}</h2>
                    <p><strong>Author:</strong> ${post.author}</p>
                    <p><strong>Date:</strong> ${post.date}</p>
                    <p>${post.content}</p>
                    <p><strong>Likes:</strong> ${post.likes || 0}</p>
                    <button onclick="likePost(${post.id})">Like</button>
                    <button onclick="deletePost(${post.id})">Delete</button>
                    <div>
                        <h3>Comments:</h3>
                        <ul>
                            ${post.comments.map(comment => `<li>${comment}</li>`).join('')}
                        </ul>
                        <input type="text" id="comment-${post.id}" placeholder="Add a comment">
                        <button onclick="addComment(${post.id})">Add Comment</button>
                    </div>
                `;
                postContainer.appendChild(postDiv);
            });
        })
        .catch(error => console.error('Error:', error));
}

function addComment(postId) {
    var baseUrl = document.getElementById('api-base-url').value;
    var comment = document.getElementById(`comment-${postId}`).value;

    fetch(`${baseUrl}/posts/${postId}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ comment: comment })
    })
    .then(response => response.json())
    .then(post => {
        console.log('Comment added:', post);
        loadPosts(); 
    })
    .catch(error => console.error('Error:', error));
}

function deletePost(postId) {
    var baseUrl = document.getElementById('api-base-url').value;

    fetch(baseUrl + '/posts/' + postId, {
        method: 'DELETE'
    })
    .then(response => {
        console.log('Post deleted:', postId);
        loadPosts(); 
    })
    .catch(error => console.error('Error:', error));  
}

function likePost(postId) {
    var baseUrl = document.getElementById('api-base-url').value;

    fetch(`${baseUrl}/posts/${postId}/like`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(post => {
        console.log('Post liked:', post);
        loadPosts(); 
    })
    .catch(error => console.error('Error:', error));
}




