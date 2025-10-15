############################################################
################### BODY TRACK // SERVER ###################
############################################################
################# CLASS: DatabaseConnector #################
############################################################

###############
### IMPORTS ###
###############
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean, desc
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session as OrmSession
from datetime import datetime
from Utilities.Logger import Logger
from Utilities.ErrorHandler import ErrorHandler, ErrorCode
from typing import Optional, List, Dict
import inspect

Base = declarative_base()

###################
### USER ENTITY ###
###################
class User(Base):
    __tablename__ = 'users'

    id            = Column(Integer, primary_key=True, autoincrement=True)
    full_name     = Column(String(100), nullable=False)
    email         = Column(String(100), nullable=False, unique=True)
    password      = Column(String(256), nullable=False)
    age           = Column(Integer)
    gender        = Column(String(10))
    date_joined   = Column(DateTime, default=datetime.now)
    is_logged_in  = Column(Boolean, default=False)
    last_login    = Column(DateTime)

    sessions = relationship("Session", back_populates="user", cascade="all, delete")

######################
### SESSION ENTITY ###
######################
class Session(Base):
    __tablename__ = 'sessions'

    id                = Column(Integer, primary_key=True, autoincrement=True)
    user_id           = Column(Integer, ForeignKey('users.id'), nullable=False)
    exercise_type     = Column(String(50), nullable=False)
    start_time        = Column(DateTime)
    end_time          = Column(DateTime)
    total_frames      = Column(Integer)
    performance_score = Column(Float)
    feedback          = Column(Text)

    user = relationship("User", back_populates="sessions")

################################
### DATABASE CONNECTOR CLASS ###
################################
class DatabaseConnector:
    """
    ### Description:
    The `DatabaseConnector` ORM-based class centralized database connector using SQLAlchemy.
    Handles all database operations (CRUD) for users and sessions,
    with consistent error handling and structured logging.
    """
    #########################
    ### CLASS CONSTRUCTOR ###
    #########################
    def __init__(self, db_path:str = "sqlite:///BodyTrack.db"):
        """
        ### Brief:
        The `__init__` method initializes the database engine and creates all required tables.

        ### Arguments:
        - `db_path` (str): Path or URI to the SQLite database file.
        """
        try:
            self.engine = create_engine(db_path, echo=False, connect_args={"check_same_thread": False})
            self.SessionFactory = sessionmaker(bind=self.engine)
            self._create_schema()
            Logger.info("DatabaseConnector was initialized successfully.")
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.DATABASE_CONNECTION_FAILED,
                origin=inspect.currentframe(),
                extra_info={"Reason": str(e)}
            )

    #####################
    ### CREATE SCHEMA ###
    #####################
    def _create_schema(self) -> None:
        """
        ### Brief:
        The `_create_schema` method ensures that all database
        tables are created according to the ORM schema.
        """
        try:
            Base.metadata.create_all(self.engine)
            Logger.info("Database schema ensured.")
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.DATABASE_SCHEMA_CREATION_FAILED,
                origin=inspect.currentframe(),
                extra_info={"Reason": str(e)}
            )

    #####################
    ### SESSION SCOPE ###
    #####################
    def _session_scope(self) -> OrmSession:
        """
        ### Brief:
        The `_session_scope` method creates and returns a new SQLAlchemy ORM session.

        ### Returns:
        A new `ORMSession` for performing transactions.
        """
        return self.SessionFactory()

    ###################
    ### INSERT USER ###
    ###################
    def insert_user(self, full_name:str, email:str, password:str,
                    age:Optional[int] = None, gender:Optional[str] = None) -> bool | ErrorCode:
        """
        ### Brief:
        The `insert_user` method inserts a new user if the
        provided email is not already registered.

        ### Arguments:
        - `full_name` (str): Full name of the user.
        - `email` (str): Unique email address of the user.
        - `password` (str): Encrypted or hashed password.
        - `age` (Optional[int]): Optional user age.
        - `gender` (Optional[str]): Optional user gender.

        ### Returns:
        - `True` on success.
        - `ErrorCode.USER_ALREADY_EXISTS` if user exists.
        - `ErrorCode.DATABASE_INSERT_FAILED` on failure.
        """
        try:
            with self._session_scope() as session:
                if session.query(User).filter_by(email=email).first():
                    Logger.warning(f"User already exists: {email}")
                    return ErrorCode.USER_ALREADY_EXISTS
                new_user = User(full_name=full_name, email=email, password=password, age=age, gender=gender)
                session.add(new_user)
                session.commit()

                # Performed successfully.
                Logger.info(f"New user registered: {email}")
                return True
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.DATABASE_INSERT_FAILED,
                origin="DatabaseConnector.insert_user",
                extra_info={"Reason": str(e), "Email": email}
            )
            return ErrorCode.DATABASE_INSERT_FAILED

    ##################
    ### LOGIN USER ###
    ##################
    def login_user(self, email:str, password:str) -> int | ErrorCode:
        """
        ### Brief:
        The `login_user` method validates user credentials and updates login status.

        ### Arguments:
        - `email` (str): The user's email.
        - `password` (str): The user's password (hashed).

        ### Returns:
        - User ID on success.
        - `ErrorCode.USER_INVALID_CREDENTIALS` if invalid credentials.
        - `ErrorCode.DATABASE_QUERY_FAILED` on DB failure.
        """
        try:
            with self._session_scope() as session:
                user = session.query(User).filter_by(email=email, password=password).first()
                # If no user exists for the given credetials.
                if not user:
                    Logger.warning(f"Invalid credentials for {email}")
                    return ErrorCode.USER_INVALID_CREDENTIALS
                
                # If the found user is already logged in.
                if user.is_logged_in is True:
                    Logger.warning(f"The user with email {email} is already logged in")
                    return ErrorCode.USER_IS_ALREADY_LOGGED_IN

                # Logging the user in.
                user.is_logged_in = True
                user.last_login = datetime.now()
                session.commit()

                # Performed successfully.
                Logger.info(f"User {email} (id: {user.id}) logged in successfully.")
                return user.id
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.DATABASE_QUERY_FAILED,
                origin=inspect.currentframe,
                extra_info={"Reason": str(e), "Email": email}
            )
            return ErrorCode.DATABASE_QUERY_FAILED

    ###################
    ### LOGOUT USER ###
    ###################
    def logout_user(self, user_id:int) -> bool | ErrorCode:
        """
        ### Brief:
        The `logout_user` method marks a user as logged out.

        ### Arguments:
        - `user_id` (int): ID of the user to log out.

        ### Returns:
        - `True` on success.
        - `ErrorCode.USER_NOT_FOUND` if user not found.
        - `ErrorCode.DATABASE_UPDATE_FAILED` on DB error.
        """
        try:
            with self._session_scope() as session:
                user = session.query(User).filter_by(id=user_id).first()
                # If the given user id is invalid.
                if not user:
                    Logger.warning(f"The user {user_id} is not found in the database.")
                    return ErrorCode.USER_NOT_FOUND
                
                # If the user is not logged in at all.
                if user.is_logged_in is False:
                    Logger.warning(f"The user {user_id} is not logged in. Can't be logged out.")
                    return ErrorCode.USER_IS_NOT_LOGGED_IN
                
                user.is_logged_in = False
                session.commit()

                # Performed successfully.
                Logger.info(f"User ID {user_id} logged out.")
                return True
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.DATABASE_UPDATE_FAILED,
                origin=inspect.currentframe(),
                extra_info={"Reason": str(e), "User ID": user_id}
            )
            return ErrorCode.DATABASE_UPDATE_FAILED

    ###################
    ### DELETE USER ###
    ###################
    def delete_user(self, user_id:int) -> bool | ErrorCode:
        """
        ### Brief:
        The `delete_user` method deletes a user and all associated sessions.

        ### Arguments:
        - `user_id` (int): ID of the user to delete.

        ### Returns:
        - `True` on success.
        - `ErrorCode.USER_NOT_FOUND` if user not found.
        - `ErrorCode.DATABASE_DELETE_FAILED` on DB failure.
        """
        try:
            with self._session_scope() as session:
                user = session.query(User).filter_by(id=user_id).first()
                if not user:
                    return ErrorCode.USER_NOT_FOUND
                session.delete(user)
                session.commit()

                # Performed successfully.
                Logger.info(f"User ID {user_id} deleted.")
                return True
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.DATABASE_DELETE_FAILED,
                origin=inspect.currentframe(),
                extra_info={"Reason": str(e), "User ID": user_id}
            )
            return ErrorCode.DATABASE_DELETE_FAILED

    #####################
    ### GET USER INFO ###
    #####################
    def get_user_info(self, user_id:int) -> Dict | ErrorCode:
        """
        ### Brief:
        The `get_user_info` method retrieves basic information about a user.

        ### Arguments:
        - `user_id` (int): ID of the user.

        ### Returns:
        - Dictionary with user information.
        - `ErrorCode.USER_NOT_FOUND` if user not found.
        - `ErrorCode.DATABASE_QUERY_FAILED` on DB error.
        """
        try:
            with self._session_scope() as session:
                user = session.query(User).filter_by(id=user_id).first()
                if not user:
                    return ErrorCode.USER_NOT_FOUND
                
                # Returning the dictionary.
                return {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "age": user.age,
                    "gender": user.gender,
                    "is_logged_in": user.is_logged_in,
                    "last_login": str(user.last_login) if user.last_login else None,
                    "date_joined": str(user.date_joined)
                }
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.DATABASE_QUERY_FAILED,
                origin=inspect.currentframe(),
                extra_info={"Reason": str(e), "User ID": user_id}
            )
            return ErrorCode.DATABASE_QUERY_FAILED

    ######################
    ### INSERT SESSION ###
    ######################
    def insert_session(self, user_id:int, exercise_type:str, start_time:datetime,
                       end_time:datetime, total_frames:int, performance_score:float,
                       feedback:str) -> bool | ErrorCode:
        """
        ### Brief:
        The `insert_session` method inserts a completed session record for a user.

        ### Arguments:
        - `user_id` (int): ID of the user owning this session.
        - `exercise_type` (str): Type of exercise performed.
        - `start_time` (datetime): Start timestamp.
        - `end_time` (datetime): End timestamp.
        - `total_frames` (int): Number of analyzed frames.
        - `performance_score` (float): Calculated performance metric.
        - `feedback` (str): JSON/text feedback data.

        ### Returns:
        - `True` on success.
        - `ErrorCode.USER_NOT_FOUND` if user does not exist.
        - `ErrorCode.DATABASE_INSERT_FAILED` on DB failure.
        """
        try:
            with self._session_scope() as session:
                if not session.query(User).filter_by(id=user_id).first():
                    return ErrorCode.USER_NOT_FOUND

                new_sess = Session(
                    user_id=user_id,
                    exercise_type=exercise_type,
                    start_time=start_time,
                    end_time=end_time,
                    total_frames=total_frames,
                    performance_score=performance_score,
                    feedback=feedback
                )
                session.add(new_sess)
                session.commit()

                # Performed successfully.
                Logger.info(f"Inserted session for user {user_id} ({exercise_type})")
                return True
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.DATABASE_INSERT_FAILED,
                origin=inspect.currentframe(),
                extra_info={"Reason": str(e), "User ID": user_id}
            )
            return ErrorCode.DATABASE_INSERT_FAILED

    ######################
    ### GET SESSIONS   ###
    ######################
    def get_user_sessions(
        self,
        user_id: int,
        order_by_date: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict] | ErrorCode:
        """
        ### Brief:
        Retrieves all sessions for a specific user.

        ### Arguments:
        - `user_id`: The user whose sessions to retrieve.
        - `order_by_date`: If True, sorts sessions by most recent.
        - `limit`: Optional limit on number of sessions returned.

        ### Returns:
        - List of session dictionaries.
        - `ErrorCode.USER_NOT_FOUND` if user not found.
        - `ErrorCode.DATABASE_QUERY_FAILED` on DB failure.
        """
        try:
            with self._session_scope() as session:
                if not session.query(User).filter_by(id=user_id).first():
                    return ErrorCode.USER_NOT_FOUND

                query = session.query(Session).filter_by(user_id=user_id)
                if order_by_date:
                    query = query.order_by(desc(Session.start_time))
                if limit:
                    query = query.limit(limit)
                sessions = query.all()

                return [{
                    "id": s.id,
                    "exercise_type": s.exercise_type,
                    "start_time": str(s.start_time),
                    "end_time": str(s.end_time),
                    "performance_score": s.performance_score,
                    "total_frames": s.total_frames
                } for s in sessions]
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.DATABASE_QUERY_FAILED,
                origin="DatabaseConnector.get_user_sessions",
                extra_info={"Reason": str(e), "User ID": user_id}
            )
            return ErrorCode.DATABASE_QUERY_FAILED

    ######################
    ### DELETE SESSIONS ###
    ######################
    def delete_user_sessions(self, user_id: int) -> bool | ErrorCode:
        """
        ### Brief:
        Deletes all session records associated with a given user.

        ### Arguments:
        - `user_id`: The ID of the user whose session history should be deleted.

        ### Returns:
        - `True` on success.
        - `ErrorCode.USER_NOT_FOUND` if user not found.
        - `ErrorCode.DATABASE_DELETE_FAILED` on DB failure.
        """
        try:
            with self._session_scope() as session:
                if not session.query(User).filter_by(id=user_id).first():
                    return ErrorCode.USER_NOT_FOUND
                deleted = session.query(Session).filter_by(user_id=user_id).delete()
                session.commit()
                Logger.info(f"Deleted {deleted} sessions for user {user_id}")
                return True
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.DATABASE_DELETE_FAILED,
                origin="DatabaseConnector.delete_user_sessions",
                extra_info={"Reason": str(e), "User ID": user_id}
            )
            return ErrorCode.DATABASE_DELETE_FAILED

    ######################
    ### CLOSE ENGINE   ###
    ######################
    def close_engine(self) -> None:
        """
        ### Brief:
        Closes all active database connections.
        """
        try:
            self.engine.dispose()
            Logger.info("Database engine closed.")
        except Exception as e:
            ErrorHandler.handle(
                error=ErrorCode.DATABASE_CLOSE_FAILED,
                origin="DatabaseConnector.close_engine",
                extra_info={"Reason": str(e)}
            )
