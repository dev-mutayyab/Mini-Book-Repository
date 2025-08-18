from typing import Annotated
from fastapi import APIRouter, Depends, status, BackgroundTasks, UploadFile, File
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.dependencies.auth import get_current_user, UserInfo
from app.utils.response import success_response, error_response
from app.services.books import BookService
from app.schemas.books import CreateBook, UpdateBook

router = APIRouter()


@router.post("/books")
async def create_book(
    book_data: CreateBook, user_info: UserInfo = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Creates a new book.

    Args:

        book_data (CreateBook): The data for the new book.
        user_info (UserInfo, optional): The user information. Defaults to the current user.
        db (Session, optional): The database session. Defaults to the database session dependency.

    Returns:

        JSONResponse: The JSON response containing the status code, message, and data.

    Raises:

        HTTPException: If there is an error creating the book.
    """
    try:
        book_service = BookService(db)
        response = await book_service.create_book(book_data)
    except Exception as e:
        return error_response(
            message=f"Error creating book: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return success_response(
        message="Book created successfully",
        data=jsonable_encoder(response),
        status_code=status.HTTP_201_CREATED,
    )


@router.put("/books/{book_id}")
async def update_book(
    book_id: str, book_data: UpdateBook, user_info: UserInfo = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Updates a book with the given ID using the provided data.

    Args:

        book_id (str): The ID of the book to update.
        book_data (UpdateBook): The data to update the book with.
        user_info (UserInfo, optional): The user information. Defaults to the current user.
        db (Session, optional): The database session. Defaults to the database session dependency.

    Returns:

        JSONResponse: The JSON response containing the status code, message, and data.

    Raises:

        HTTPException: If there is an error updating the book.
    """
    try:
        book_service = BookService(db)
        response = await book_service.update_book(book_id, book_data)
    except Exception as e:
        return error_response(
            message=f"Error updating book: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return success_response(
        message="Book updated successfully",
        data=jsonable_encoder(response),
        status_code=status.HTTP_200_OK,
    )


@router.get("/books/{book_id}")
async def get_book(book_id: str, user_info: UserInfo = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get a book by ID.

    Args:

        book_id (str): The ID of the book to retrieve.
        user_info (UserInfo, optional): The user information. Defaults to the current user.
        db (Session, optional): The database session. Defaults to the database session dependency.

    Returns:

        JSONResponse: The JSON response containing the status code, message, and data.

    Raises:

        HTTPException: If there is an error retrieving the book.
    """
    try:
        book_service = BookService(db)
        response = await book_service.get_book(book_id)
    except Exception as e:
        return error_response(
            message=f"Error getting book: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return success_response(
        message="Book retrieved successfully",
        data=jsonable_encoder(response),
        status_code=status.HTTP_200_OK,
    )


@router.delete("/books/{book_id}")
async def delete_book(book_id: str, user_info: UserInfo = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Delete a book by ID.

    Args:

        book_id (str): The ID of the book to delete.
        user_info (UserInfo, optional): The user information. Defaults to the current user.
        db (Session, optional): The database session. Defaults to the database session dependency.

    Returns:

        JSONResponse: The JSON response containing the status code, message, and data.

    Raises:

        HTTPException: If there is an error deleting the book.
    """
    try:
        book_service = BookService(db)
        response = await book_service.delete_book(book_id)
    except Exception as e:
        return error_response(
            message=f"Error deleting book: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return success_response(
        message="Book deleted successfully",
        data=jsonable_encoder(response),
        status_code=status.HTTP_200_OK,
    )


@router.get("/books")
async def show_all_books(
    search: Annotated[str, None] = None,
    offset: int = 0,
    limit: int = 10,
    user_info: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get books based on the given search query and pagination parameters.

    Args:

        search (str, optional): The search query to filter books by title or author. Defaults to None.
        offset (int, optional): The offset for pagination. Defaults to 0.
        limit (int, optional): The limit for pagination. Defaults to 10.
        user_info (UserInfo, optional): The user information. Defaults to the current user.
        db (Session, optional): The database session. Defaults to the database session dependency.

    Returns:

        JSONResponse: The JSON response containing the status code, message, and data.
            If successful, the data contains a list of books matching the search query, along with pagination metadata.
    """
    try:
        book_service = BookService(db)
        response = await book_service.get_books(search=search, offset=offset, limit=limit)
    except Exception as e:
        return error_response(
            message=f"Error showing books: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return success_response(
        message="Books shown successfully",
        data=[jsonable_encoder(responses) for responses in response],
        status_code=status.HTTP_200_OK,
    )


@router.post("/books/upload")
async def upload_books_csv(
    file: UploadFile = File(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user_info: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a CSV file containing books information for addition into the database.

    Args:

        file (UploadFile): The CSV file to be uploaded.
        background_tasks (BackgroundTasks): The background tasks dependency.
        user_info (UserInfo): The user information dependency.
        db (Session): The database session dependency.

    Returns:

        JSONResponse: A JSON response indicating the status of the upload.

    Raises:

        HTTPException: If there is an error uploading the CSV file.

    """
    try:
        book_service = BookService(db)
        response = await book_service.upload_file_for_books_addition(
            file=file, background_tasks=background_tasks, user_id=user_info.user_id
        )
        return success_response(
            message="CSV upload scheduled",
            data=jsonable_encoder(response),
            status_code=status.HTTP_202_ACCEPTED,
        )
    except Exception as e:
        return error_response(
            message=f"Error uploading CSV file: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/books/upload/{upload_id}")
async def get_upload_status(
    upload_id: str, user_info: UserInfo = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Retrieve the status of a file upload for adding books to the database.

    Args:

        upload_id (str): The ID of the upload.
        user_info (UserInfo): The user information dependency.
        db (Session): The database session dependency.

    Returns:

        JSONResponse: The JSON response containing the status code, message, and data.
            If successful, the data contains the upload status, errors, and upload ID.

    Raises:

        HTTPException: If there is an error retrieving the upload status.
    """
    try:
        book_service = BookService(db)
        status_data = await book_service.get_upload_status(upload_id, user_info.user_id)
        status_message = {
            "pending": "Your file is still being processed. Please check again later.",
            "success": "Your file was processed successfully.",
            "failed": "Your file processing failed. Check the errors for details.",
        }.get(status_data["status"], "Unknown status")
        return success_response(
            message=status_message,
            data={"upload_id": upload_id, "status": status_data["status"], "errors": status_data["errors"]},
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(
            message=f"Error retrieving upload status: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
