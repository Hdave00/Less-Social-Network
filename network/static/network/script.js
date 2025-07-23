document.addEventListener("DOMContentLoaded", function () {

    // event listener for editing posts and liking
    document.querySelectorAll(".edit-label").forEach(button => {
        button.addEventListener("click", () => edit_post(button));
    });

    // using event delegation
    document.body.addEventListener("click", function (event) {
        if (event.target.closest(".like-button")) {
            toggle_like(event.target.closest(".like-button"));
        }
    });

    console.log("Event delegation for like buttons set up.");

    // Tarot card selection
    const tarotModal = document.getElementById("tarotModal");
    if (tarotModal) {
        tarotModal.querySelectorAll(".tarot-option").forEach(button => {
            button.addEventListener("click", function () {
                const cardId = this.dataset.cardId;
                document.getElementById("tarotCardInput").value = cardId;

                // Close modal after selection
                const modalInstance = bootstrap.Modal.getInstance(tarotModal);
                modalInstance.hide();
            });
        });
    }
});


// 1- Edit post function
function edit_post(button) {
    // get closest card
    const post_div = button.closest(".card");
    const post_id = button.dataset.postId;
    const post_content_element = post_div.querySelector(".post-context");

    // get only plaintext
    const original_content = post_content_element.textContent.trim();

    // checking if editing div already exists (cause html issues)
    if (post_div.querySelector(`#post-${post_id}-edit`)) return;

    // replace content with text area
    post_content_element.innerHTML = `
        <textarea id="post-${post_id}-edit" class="form-control mb-2">${original_content}</textarea>
        <div class="d-flex justify-content-end mt-2">
            <button class="btn btn-secondary mx-2 cancel-button">Cancel</button>
            <button class="btn btn-primary save-button">Save</button>
        </div>`;

    // new buttons to show
    const cancel_button = post_content_element.querySelector(".cancel-button");
    const save_button = post_content_element.querySelector(".save-button");

    // restore original content when cancel button clicked
    cancel_button.addEventListener("click", function () {
        post_content_element.innerHTML = original_content;
    });

    save_button.addEventListener("click", function () {
        save_edited_post(post_id, post_content_element);
    });
}

// 2- Save edited post function
function save_edited_post(post_id, post_content_element) {
    const edited_content = document.querySelector(`#post-${post_id}-edit`).value.trim();

    fetch(`/post/${post_id}/edit`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({ content: edited_content }),
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);
        post_content_element.innerHTML = edited_content;
    })
    .catch(error => console.error("Error:", error));
}


// 4- like/unlike functionality
function toggle_like(button){

    console.log("like button clicked")
    // the like count must be updated for each html element, learnt that from the ddb, this basically gives a number beside the icon by making an
    // API fetch/call and getting the liked and appending the html element
    const post_id = button.dataset.postId;
    const like_count_element = document.querySelector(`#like-count-${post_id}`);
    const like_icon = document.querySelector(`#like-icon-${post_id}`);

    // fetch request to API, use POST to send data to python backend to update like status
    fetch(`/post/${post_id}/like`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);

        // update like count
        like_count_element.textContent = result.likes;

        if (result.liked_by_user) {
            like_icon.classList.remove("bi-heart");
            like_icon.classList.add("bi-heart-fill", "text-danger");
        } else {
            like_icon.classList.remove("bi-heart-fill", "text-danger");
            like_icon.classList.add("bi-heart");
        }
    })
    .catch(error => console.error("Error:", error));
}


// 5- function for dynamically creating new div each time for letting a user make another post and asynchonously appending to the page after submission
function createPostElement(post) {

    // creating a div, specifically the div that contains the details of the post
    const post_div = document.createElement("div");
    post_div.className = "container border rounded mx-4 my-2 post-div";

    // html template copied from the html page to be rendered in once a new post is made
    post_div.innerHTML = `
        <input type="hidden" class="post-id" value="${post.id}" />
        <div class="row m-2">
            <div class="col font-weight-bold"><a href="/user/${post.user}">${post.user}</a></div>
        </div>
        <div class="row mx-2">
            <div class="col"><span class="edit-label">edit</span></div>
        </div>
        <div class="row m-2">
            <div class="col post-context">${post.content}</div>
        </div>
        <div class="row m-2">
            <div class="col post-date">${post.timestamp}</div>
        </div>
        <div class="row m-2">
            <div class="col">
                <span class="like-count-label" id="like-count-${post.id}">${post.like_count}</span>
                <button class="like-button border-0 bg-transparent" data-post-id="${post.id}">
                    <i class="bi bi-heart" id="like-icon-${post.id}"></i>
                </button>
            </div>
        </div>
    `;

    // calling edit_post and toggle_like function each time either the edit button or like button is clicked
    post_div.querySelector(".edit-label").addEventListener("click", () => edit_post(post_div.querySelector(".edit-label")));
    post_div.querySelector(".like-button").addEventListener("click", () => toggle_like(post_div.querySelector(".like-button")));

    // returning the updated div element for the post
    return post_div;
}


// getCookie function from Django docs (needed for csrf)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
