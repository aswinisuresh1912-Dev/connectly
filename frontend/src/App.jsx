import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [users, setUsers] = useState([]);
  const [posts, setPosts] = useState([]);

  const [currentUser, setCurrentUser] = useState(null);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [newPost, setNewPost] = useState("");
  const [commentText, setCommentText] = useState({});

  const [followingUsers, setFollowingUsers] = useState([]);

  useEffect(() => {
    loadUsers();
  }, []);

  useEffect(() => {
    if (currentUser) {
      loadPosts();
      loadUsers();
    }
  }, [currentUser]);

  const loadUsers = async () => {
    try {
      const response = await fetch(
        "http://127.0.0.1:5000/users"
      );

      const data = await response.json();

      setUsers(data);
    } catch (error) {
      console.error("Error loading users:", error);
    }
  };

  const loadPosts = async () => {
    try {
      const response = await fetch(
        `http://127.0.0.1:5000/posts?user_id=${currentUser.id}`
      );

      const data = await response.json();

      setPosts(data);
    } catch (error) {
      console.error("Error loading posts:", error);
    }
  };

  const login = async (event) => {
    event.preventDefault();

    if (!username.trim() || !password) {
      alert("Please enter username and password");
      return;
    }

    try {
      const response = await fetch(
        "http://127.0.0.1:5000/login",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            username: username.trim(),
            password: password
          })
        }
      );

      const data = await response.json();

      if (!response.ok) {
        alert(data.error || "Login failed");
        return;
      }

      setCurrentUser(data.user);

      setUsername("");
      setPassword("");

    } catch (error) {
      console.error("Login error:", error);
      alert("Cannot connect to the Flask server");
    }
  };

  const createPost = async () => {
    if (!newPost.trim()) {
      return;
    }

    try {
      await fetch(
        "http://127.0.0.1:5000/posts",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            content: newPost,
            user_id: currentUser.id
          })
        }
      );

      setNewPost("");

      loadPosts();

    } catch (error) {
      console.error("Error creating post:", error);
    }
  };

  const likePost = async (postId) => {
    try {
      await fetch(
        `http://127.0.0.1:5000/posts/${postId}/like`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            user_id: currentUser.id
          })
        }
      );

      loadPosts();

    } catch (error) {
      console.error("Like error:", error);
    }
  };

  const addComment = async (postId) => {
    const text = commentText[postId];

    if (!text || !text.trim()) {
      return;
    }

    try {
      await fetch(
        `http://127.0.0.1:5000/posts/${postId}/comments`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            text: text,
            user_id: currentUser.id
          })
        }
      );

      setCommentText((previousComments) => ({
        ...previousComments,
        [postId]: ""
      }));

      loadPosts();

    } catch (error) {
      console.error("Comment error:", error);
    }
  };

const followUser = async (userId) => {
  try {
    const response = await fetch(
      `http://127.0.0.1:5000/users/${userId}/follow`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          follower_id: currentUser.id
        })
      }
    );

    const data = await response.json();

    if (!response.ok) {
      alert(data.error || "Something went wrong");
      return;
    }

    // Update the current user's following count
    setCurrentUser((previousUser) => ({
      ...previousUser,
      following: data.following
    }));

    // Follow -> Following
    if (data.message === "Following") {
      setFollowingUsers((previousUsers) => [
        ...previousUsers,
        userId
      ]);
    }

    // Following -> Follow
    if (data.message === "Unfollowed") {
      setFollowingUsers((previousUsers) =>
        previousUsers.filter(
          (id) => id !== userId
        )
      );
    }

  } catch (error) {
    console.error("Follow error:", error);
  }
};
  const logout = () => {
    setCurrentUser(null);
    setPosts([]);
  };

  if (!currentUser) {
    return (
      <div className="login-page">
        <div className="login-box">

          <h1>Connectly</h1>

          <p>
            Connect. Share. Discover.
          </p>

          <form onSubmit={login}>

            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(event) =>
                setUsername(event.target.value)
              }
            />

            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
            />

            <button type="submit">
              Login
            </button>

          </form>

        </div>
      </div>
    );
  }

  return (
    <div className="app">

      <header className="navbar">

        <h1>Connectly</h1>

        <div className="nav-user">

          <strong>
            @{currentUser.username}
          </strong>

          <button onClick={logout}>
            Logout
          </button>

        </div>

      </header>

      <main className="layout">

        <aside className="sidebar">

          <div className="profile-box">

            <div className="avatar">

              {currentUser.username
                .charAt(0)
                .toUpperCase()}

            </div>

            <h2>
              @{currentUser.username}
            </h2>

            <p>
              {currentUser.bio}
            </p>

            <div className="stats">

              <span>
                <b>
                  {currentUser.followers}
                </b>
                Followers
              </span>

              <span>
                <b>
                  {currentUser.following}
                </b>
                Following
              </span>

            </div>

          </div>

          <div className="people-box">

            <h3>
              Discover People
            </h3>

            {users
              .filter(
                (user) =>
                  user.id !== currentUser.id
              )
              .map((user) => (

                <div
                  className="person"
                  key={user.id}
                >

                  <span>
                    @{user.username}
                  </span>

                  <button onClick={() => followUser(user.id)}>
                      {followingUsers.includes(user.id)
                        ? "Following"
                        : "Follow"}
                </button>

                </div>

              ))}

          </div>

        </aside>

        <section className="feed">

          <div className="create-post">

            <textarea
              placeholder="What's on your mind?"
              value={newPost}
              onChange={(event) =>
                setNewPost(event.target.value)
              }
            />

            <button onClick={createPost}>
              Post
            </button>

          </div>

          {posts.map((post) => (

            <article
              className="post"
              key={post.id}
            >

              <div className="post-header">

                <div className="avatar small">

                  {post.username
                    .charAt(0)
                    .toUpperCase()}

                </div>

                <strong>
                  @{post.username}
                </strong>

              </div>

              <p className="post-content">
                {post.content}
              </p>

              <div className="post-actions">

                <button
                  onClick={() =>
                    likePost(post.id)
                  }
                >
                  {post.liked
                    ? "❤️"
                    : "♡"}

                  {" "}

                  {post.likes}
                </button>

              </div>

              <div className="comments">

                {post.comments.map(
                  (comment) => (

                    <p
                      key={comment.id}
                    >

                      <strong>
                        @{comment.username}
                      </strong>

                      {" "}

                      {comment.text}

                    </p>

                  )
                )}

                <div className="comment-form">

                  <input
                    type="text"
                    placeholder="Write a comment..."
                    value={
                      commentText[post.id] || ""
                    }
                    onChange={(event) =>
                      setCommentText(
                        (previousComments) => ({
                          ...previousComments,
                          [post.id]:
                            event.target.value
                        })
                      )
                    }
                  />

                  <button
                    onClick={() =>
                      addComment(post.id)
                    }
                  >
                    Comment
                  </button>

                </div>

              </div>

            </article>

          ))}

        </section>

      </main>

    </div>
  );
}

export default App;