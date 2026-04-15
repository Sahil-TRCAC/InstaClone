import os
from datetime import datetime
from flask import Flask, render_template, url_for, redirect, request, jsonify, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw
import secrets
import json
import logging
from forms import LoginForm, RegisterForm, PostForm, ReelForm, CommentForm, EditProfileForm, SearchForm
from models import db, User, Post, Reel, Like, Comment, Story, Message, Notification
from config import Config
import uuid

app = Flask(__name__)
app.config.from_object(Config)

# Add context processor HERE (not in models.py)
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}  # ✅ FIXED: Added parentheses to call the function

# Configure logging to reduce noise
logging.getLogger('werkzeug').setLevel(logging.WARNING)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# ... rest of your code remains the same ...

# ... rest of your routes ...

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_picture(file, folder, size=(800, 800)):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(file.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/uploads', folder, picture_fn)
    
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    
    img = Image.open(file)
    img.thumbnail(size, Image.Resampling.LANCZOS)
    img.save(picture_path)  
    
    return picture_fn

def save_video(file, folder):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(file.filename)
    video_fn = random_hex + f_ext
    video_path = os.path.join(app.root_path, 'static/uploads', folder, video_fn)
    
    os.makedirs(os.path.dirname(video_path), exist_ok=True)
    file.save(video_path)
    
    return video_fn

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    return render_template('index.html', title='Welcome')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    
    form = RegisterForm()
    
    if form.validate_on_submit():
        # Check if user exists (validation moved from forms.py to here)
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))
        
        existing_username = User.query.filter_by(username=form.username.data).first()
        if existing_username:
            flash('Username already taken!', 'danger')
            return redirect(url_for('register'))
        
        # Create new user
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            profile_pic='default.jpg'
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form, title='Register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('feed'))
        flash('Login failed. Check username and password.', 'danger')
    
    return render_template('login.html', form=form, title='Login')

@app.route('/logout', methods=['GET', 'POST'])  # Add POST method
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('index'))


@app.route('/feed')
@login_required
def feed():
    page = request.args.get('page', 1, type=int)
    
    # Get posts from followed users and user's own posts
    following_ids = [user.id for user in current_user.following] + [current_user.id]
    posts = Post.query.filter(Post.user_id.in_(following_ids)) \
        .order_by(Post.created_at.desc()) \
        .paginate(page=page, per_page=10)
    
    # Get active stories
    active_stories = Story.query.filter(
        Story.user_id.in_(following_ids),
        Story.expires_at > datetime.utcnow()
    ).order_by(Story.created_at.desc()).all()
    
    # Get suggestions
    suggestions = User.query.filter(User.id != current_user.id) \
        .filter(~User.followers.any(id=current_user.id)) \
        .limit(5).all()
    
    return render_template('feed.html', posts=posts, 
                         stories=active_stories, 
                         suggestions=suggestions,
                         title='Feed')
from datetime import datetime, timedelta

# Add this custom filter for time_ago
@app.template_filter('time_ago')
def time_ago_filter(date):
    """Convert datetime to human readable time ago string"""
    now = datetime.utcnow()
    diff = now - date
    
    if diff < timedelta(minutes=1):
        return 'just now'
    elif diff < timedelta(hours=1):
        minutes = diff.seconds // 60
        return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
    elif diff < timedelta(days=1):
        hours = diff.seconds // 3600
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    elif diff < timedelta(days=7):
        days = diff.days
        return f'{days} day{"s" if days != 1 else ""} ago'
    elif diff < timedelta(days=30):
        weeks = diff.days // 7
        return f'{weeks} week{"s" if weeks != 1 else ""} ago'
    elif diff < timedelta(days=365):
        months = diff.days // 30
        return f'{months} month{"s" if months != 1 else ""} ago'
    else:
        years = diff.days // 365
        return f'{years} year{"s" if years != 1 else ""} ago'
    
@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        if form.image.data:
            filename = save_picture(form.image.data, 'posts')
            post = Post(
                image_url=filename,
                caption=form.caption.data,
                user=current_user
            )
            db.session.add(post)
            db.session.commit()
            flash('Your post has been created!', 'success')
            return redirect(url_for('feed'))
    return render_template('create_post.html', form=form, title='Create Post')

@app.route('/post/<int:post_id>')
@login_required
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post_detail.html', post=post, title='Post')

@app.route('/like_post/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    existing_like = Like.query.filter_by(
        user_id=current_user.id,
        post_id=post_id,
        reel_id=None
    ).first()
    
    if existing_like:
        db.session.delete(existing_like)
        liked = False
    else:
        like = Like(user_id=current_user.id, post_id=post_id)
        db.session.add(like)
        liked = True
    
    db.session.commit()
    
    return jsonify({
        'status': 'liked' if liked else 'unliked',
        'count': post.likes.count()
    })

@app.route('/comment_post/<int:post_id>', methods=['POST'])
@login_required
def comment_post(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content', '').strip()
    
    if content:
        comment = Comment(
            content=content,
            user_id=current_user.id,
            post_id=post_id
        )
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'comment': {
                'username': current_user.username,
                'profile_pic': current_user.profile_pic,
                'content': content,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })
    
    return jsonify({'success': False})

@app.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    reels = Reel.query.filter_by(user_id=user.id).order_by(Reel.created_at.desc()).all()
    
    is_following = current_user.is_following(user) if current_user != user else None
    
    return render_template('profile.html', 
                         user=user, 
                         posts=posts, 
                         reels=reels,
                         is_following=is_following,
                         title=f'{username}\'s Profile')

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        if form.profile_pic.data:
            filename = save_picture(form.profile_pic.data, 'profiles', size=(400, 400))
            current_user.profile_pic = filename
        
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.bio = form.bio.data
        
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('profile', username=current_user.username))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.bio.data = current_user.bio
    
    return render_template('edit_profile.html', form=form, title='Edit Profile')

@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    if user == current_user:
        return jsonify({'error': 'You cannot follow yourself'}), 400
    
    if current_user.is_following(user):
        current_user.unfollow(user)
        following = False
    else:
        current_user.follow(user)
        following = True
    
    db.session.commit()
    
    return jsonify({
        'following': following,
        'followers_count': user.followers.count(),
        'following_count': user.following.count()
    })

@app.route('/reels')
@login_required
def reels():
    page = request.args.get('page', 1, type=int)
    reels_list = Reel.query.order_by(Reel.created_at.desc()) \
        .paginate(page=page, per_page=9)
    
    return render_template('reels.html', reels=reels_list, title='Reels')

@app.route('/create_reel', methods=['GET', 'POST'])
@login_required
def create_reel():
    form = ReelForm()
    if form.validate_on_submit():
        if form.video.data:
            filename = save_video(form.video.data, 'reels')
            reel = Reel(
                video_url=filename,
                caption=form.caption.data,
                user=current_user
            )
            db.session.add(reel)
            db.session.commit()
            flash('Your reel has been uploaded!', 'success')
            return redirect(url_for('reels'))
    
    return render_template('create_reel.html', form=form, title='Create Reel')

@app.route('/like_reel/<int:reel_id>', methods=['POST'])
@login_required
def like_reel(reel_id):
    reel = Reel.query.get_or_404(reel_id)
    existing_like = Like.query.filter_by(
        user_id=current_user.id,
        reel_id=reel_id,
        post_id=None
    ).first()
    
    if existing_like:
        db.session.delete(existing_like)
        liked = False
    else:
        like = Like(user_id=current_user.id, reel_id=reel_id)
        db.session.add(like)
        liked = True
    
    db.session.commit()
    
    return jsonify({
        'status': 'liked' if liked else 'unliked',
        'count': reel.likes.count()
    })

@app.route('/comment_reel/<int:reel_id>', methods=['POST'])
@login_required
def comment_reel(reel_id):
    reel = Reel.query.get_or_404(reel_id)
    content = request.form.get('content', '').strip()
    
    if content:
        comment = Comment(
            content=content,
            user_id=current_user.id,
            reel_id=reel_id
        )
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'comment': {
                'username': current_user.username,
                'profile_pic': current_user.profile_pic,
                'content': content,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })
    
    return jsonify({'success': False})

@app.route('/stories')
@login_required
def stories():
    # Get stories from followed users
    following_ids = [user.id for user in current_user.following]
    stories = Story.query.filter(
        Story.user_id.in_(following_ids),
        Story.expires_at > datetime.utcnow()
    ).order_by(Story.created_at.desc()).all()
    
    return render_template('stories.html', stories=stories, title='Stories')

@app.route('/create_story', methods=['POST'])
@login_required
def create_story():
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif'}):
            filename = save_picture(file, 'stories', size=(1080, 1920))
            
            story = Story(
                image_url=filename,
                user=current_user
            )
            db.session.add(story)
            db.session.commit()
            
            return jsonify({'success': True, 'story_id': story.id})
    
    return jsonify({'success': False, 'error': 'Invalid file'})

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    results = []
    
    if query:
        # Search users
        users = User.query.filter(
            (User.username.ilike(f'%{query}%')) |
            (User.email.ilike(f'%{query}%'))
        ).limit(20).all()
        
        # Search posts
        posts = Post.query.filter(
            Post.caption.ilike(f'%{query}%')
        ).limit(20).all()
        
        results = {
            'users': users,
            'posts': posts
        }
    
    return render_template('search.html', results=results, query=query, title='Search')

@app.route('/api/search', methods=['GET'])
@login_required
def api_search():
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify({'users': [], 'posts': []})
    
    users = User.query.filter(User.username.ilike(f'%{query}%')) \
        .limit(10) \
        .all()
    
    user_list = [{
        'id': user.id,
        'username': user.username,
        'profile_pic': user.profile_pic,
        'is_following': current_user.is_following(user)
    } for user in users]
    
    return jsonify({'users': user_list})

@app.route('/direct')
@login_required
def direct():
    # Get conversations
    sent_messages = Message.query.filter_by(sender_id=current_user.id).all()
    received_messages = Message.query.filter_by(receiver_id=current_user.id).all()
    
    all_messages = sent_messages + received_messages
    user_ids = set()
    
    for msg in all_messages:
        user_ids.add(msg.sender_id)
        user_ids.add(msg.receiver_id)
    
    user_ids.discard(current_user.id)
    conversations = User.query.filter(User.id.in_(user_ids)).all()
    
    return render_template('direct.html', conversations=conversations, title='Messages')

@app.route('/direct/<username>', methods=['GET', 'POST'])
@login_required
def chat(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if content:
            message = Message(
                content=content,
                sender_id=current_user.id,
                receiver_id=user.id
            )
            db.session.add(message)
            db.session.commit()
            return redirect(url_for('chat', username=username))
    
    # Get messages between current user and this user
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user.id)) |
        ((Message.sender_id == user.id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()
    
    return render_template('chat.html', user=user, messages=messages, title=f'Chat with {username}')

@app.route('/api/messages/<int:user_id>', methods=['GET'])
@login_required
def api_messages(user_id):
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()
    
    messages_list = [{
        'id': msg.id,
        'content': msg.content,
        'sender_id': msg.sender_id,
        'receiver_id': msg.receiver_id,
        'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'is_own': msg.sender_id == current_user.id
    } for msg in messages]
    
    return jsonify(messages_list)

@app.route('/api/send_message', methods=['POST'])
@login_required
def api_send_message():
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'success': False, 'error': 'Message cannot be empty'})
    
    message = Message(
        content=content,
        sender_id=current_user.id,
        receiver_id=receiver_id
    )
    db.session.add(message)
    db.session.commit()
    
    return jsonify({'success': True, 'message_id': message.id})

@app.route('/explore')
@login_required
def explore():
    # Get popular posts (based on likes)
    popular_posts = Post.query.order_by(
        db.func.count(Post.likes).desc()
    ).limit(12).all()
    
    # Get suggested users
    suggested_users = User.query.filter(
        User.id != current_user.id,
        ~User.followers.any(id=current_user.id)
    ).order_by(db.func.random()).limit(6).all()
    
    return render_template('explore.html', 
                         popular_posts=popular_posts, 
                         suggested_users=suggested_users,
                         title='Explore')



@app.route('/notifications')
@login_required
def notifications():
    # Get recent activities
    notifications = []
    
    # Follow notifications - FIXED: Use the followers association table
    # Get users who recently followed the current user
    from models import followers  # Import the association table
    
    # Query to get recent followers
    recent_follower_ids = db.session.query(followers.c.follower_id).filter(
        followers.c.followed_id == current_user.id
    ).order_by(followers.c.created_at.desc()).limit(20).all()
    
    recent_follower_ids = [id_tuple[0] for id_tuple in recent_follower_ids]
    recent_followers = User.query.filter(User.id.in_(recent_follower_ids)).all()
    
    # Like notifications
    user_post_ids = [post.id for post in current_user.posts]
    recent_likes = Like.query.filter(Like.post_id.in_(user_post_ids)) \
        .filter(Like.user_id != current_user.id) \
        .order_by(Like.created_at.desc()) \
        .limit(20) \
        .all()
    
    # Comment notifications
    recent_comments = Comment.query.filter(Comment.post_id.in_(user_post_ids)) \
        .filter(Comment.user_id != current_user.id) \
        .order_by(Comment.created_at.desc()) \
        .limit(20) \
        .all()
    
    # Combine and sort all notifications
    for follower in recent_followers:
        # Get the follow timestamp
        follow_time = db.session.query(followers.c.created_at).filter(
            followers.c.follower_id == follower.id,
            followers.c.followed_id == current_user.id
        ).scalar()
        
        notifications.append({
            'type': 'follow',
            'user': follower,
            'created_at': follow_time or datetime.utcnow(),
            'read': False
        })
    
    for like in recent_likes:
        notifications.append({
            'type': 'like',
            'user': like.user,
            'post': like.post,
            'created_at': like.created_at,
            'read': False
        })
    
    for comment in recent_comments:
        notifications.append({
            'type': 'comment',
            'user': comment.user,
            'post': comment.post,
            'content': comment.content[:50],
            'created_at': comment.created_at,
            'read': False
        })
    
    # Sort by date
    notifications.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render_template('notifications.html', 
                         notifications=notifications[:50],
                         title='Notifications')    
    # Like notifications
    user_post_ids = [post.id for post in current_user.posts]
    recent_likes = Like.query.filter(Like.post_id.in_(user_post_ids)) \
        .filter(Like.user_id != current_user.id) \
        .order_by(Like.created_at.desc()) \
        .limit(20) \
        .all()
    
    # Comment notifications
    recent_comments = Comment.query.filter(Comment.post_id.in_(user_post_ids)) \
        .filter(Comment.user_id != current_user.id) \
        .order_by(Comment.created_at.desc()) \
        .limit(20) \
        .all()
    
    # Combine and sort all notifications
    for follow in recent_follows:
        notifications.append({
            'type': 'follow',
            'user': follow.follower,
            'created_at': follow.created_at,
            'read': False
        })
    
    for like in recent_likes:
        notifications.append({
            'type': 'like',
            'user': like.user,
            'post': like.post,
            'created_at': like.created_at,
            'read': False
        })
    
    for comment in recent_comments:
        notifications.append({
            'type': 'comment',
            'user': comment.user,
            'post': comment.post,
            'content': comment.content[:50],
            'created_at': comment.created_at,
            'read': False
        })
    
    # Sort by date
    notifications.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render_template('notifications.html', 
                         notifications=notifications[:50],
                         title='Notifications')

@app.route('/save_post/<int:post_id>', methods=['POST'])
@login_required
def save_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if post in current_user.saved_posts:
        current_user.saved_posts.remove(post)
        saved = False
    else:
        current_user.saved_posts.append(post)
        saved = True
    
    db.session.commit()
    
    return jsonify({'saved': saved})

@app.route('/saved')
@login_required
def saved_posts():
    saved = current_user.saved_posts
    return render_template('saved.html', saved_posts=saved, title='Saved Posts')

@app.route('/share_post/<int:post_id>', methods=['POST'])
@login_required
def share_post(post_id):
    post = Post.query.get_or_404(post_id)
    share_url = url_for('post_detail', post_id=post_id, _external=True)
    
    # In a real app, you would integrate with social media APIs
    # For now, just return the shareable URL
    return jsonify({
        'success': True,
        'share_url': share_url,
        'message': 'Post shared successfully!'
    })

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Create database tables and default data
with app.app_context():
    db.create_all()
    
    # Create default profile picture if it doesn't exist
    default_pic_path = os.path.join(app.root_path, 'static/uploads/profiles/default.jpg')
    if not os.path.exists(default_pic_path):
        os.makedirs(os.path.dirname(default_pic_path), exist_ok=True)
        img = Image.new('RGB', (400, 400), color='#6c63ff')
        d = ImageDraw.Draw(img)
        d.text((150, 180), "USER", fill=(255, 255, 255))
        img.save(default_pic_path)
    
    # Create test users if none exist
    if User.query.count() == 0:
        test_users = [
            {'username': 'admin', 'email': 'admin@gmail.com', 'password': 'password123'},
            {'username': 'user1', 'email': 'user1@gmail.com', 'password': 'password123'},
            {'username': 'user2', 'email': 'user2@gmail.com', 'password': 'password123'},
            {'username': 'johndoe', 'email': 'john@gmail.com', 'password': 'password123'},
            {'username': 'janedoe', 'email': 'jane@gmail.com', 'password': 'password123'},
        ]
        
        for user_data in test_users:
            if not User.query.filter_by(email=user_data['email']).first():
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=generate_password_hash(user_data['password']),
                    profile_pic='default.jpg'
                )
                db.session.add(user)
        
        db.session.commit()
        print("✅ Created test users")
    
    print("✅ Database initialized successfully!")
@app.route('/api/check-username')
def check_username():
    username = request.args.get('username', '')
    if not username or len(username) < 3:
        return jsonify({'available': False, 'error': 'Username too short'})
    
    user = User.query.filter_by(username=username).first()
    
    if user:
        # Generate suggestions
        suggestions = []
        base_name = username
        for i in range(1, 4):
            suggestions.append(f"{base_name}{i}")
            suggestions.append(f"{base_name}_{i}")
            suggestions.append(f"{base_name}.{i}")
        
        return jsonify({
            'available': False,
            'suggestions': suggestions[:6]  # Limit to 6 suggestions
        })
    
    return jsonify({'available': True})
if __name__ == '__main__':
    import os

    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.ERROR)

    # ✅ Only run once (important fix)
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        print("\n" + "="*50)
        print("🚀 InstaClone is starting...")
        print("🌐 Local URL: http://127.0.0.1:5000")
        
        print("="*50 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)