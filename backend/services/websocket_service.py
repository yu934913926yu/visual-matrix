from flask_socketio import SocketIO, emit, join_room, leave_room
import logging

logger = logging.getLogger(__name__)

class WebSocketService:
    socketio = None
    connected_users = {}  # {user_id: [session_ids]}
    
    @classmethod
    def init_app(cls, app):
        cls.socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
        cls._register_events()
    
    @classmethod
    def _register_events(cls):
        """注册WebSocket事件"""
        
        @cls.socketio.on('connect')
        def handle_connect(auth):
            logger.info(f"客户端连接: {auth}")
            emit('connected', {'status': 'success'})
        
        @cls.socketio.on('disconnect')
        def handle_disconnect():
            logger.info("客户端断开连接")
        
        @cls.socketio.on('join_user_room')
        def handle_join_user_room(data):
            """用户加入自己的房间，用于接收个人消息"""
            user_id = data.get('user_id')
            if user_id:
                room = f"user_{user_id}"
                join_room(room)
                
                # 记录连接的用户
                if user_id not in cls.connected_users:
                    cls.connected_users[user_id] = []
                cls.connected_users[user_id].append(request.sid)
                
                emit('joined_room', {'room': room})
                logger.info(f"用户 {user_id} 加入房间 {room}")
        
        @cls.socketio.on('leave_user_room')
        def handle_leave_user_room(data):
            """用户离开房间"""
            user_id = data.get('user_id')
            if user_id:
                room = f"user_{user_id}"
                leave_room(room)
                
                # 移除连接记录
                if user_id in cls.connected_users:
                    cls.connected_users[user_id] = [
                        sid for sid in cls.connected_users[user_id] 
                        if sid != request.sid
                    ]
                    if not cls.connected_users[user_id]:
                        del cls.connected_users[user_id]
                
                emit('left_room', {'room': room})
                logger.info(f"用户 {user_id} 离开房间 {room}")
    
    @classmethod
    def emit_to_user(cls, user_id: int, event: str, data: dict):
        """向特定用户发送消息"""
        if cls.socketio:
            room = f"user_{user_id}"
            cls.socketio.emit(event, data, room=room)
            logger.info(f"向用户 {user_id} 发送事件 {event}: {data}")
    
    @classmethod
    def emit_to_all(cls, event: str, data: dict):
        """向所有连接的客户端发送消息"""
        if cls.socketio:
            cls.socketio.emit(event, data)
            logger.info(f"向所有用户发送事件 {event}: {data}")
    
    @classmethod
    def get_connected_users(cls):
        """获取当前连接的用户列表"""
        return list(cls.connected_users.keys())