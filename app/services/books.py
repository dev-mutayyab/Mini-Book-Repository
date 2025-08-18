import os, csv, logging, uuid, json
from pathlib import Path
from typing import Annotated
from datetime import datetime, timezone, date
from fastapi import status, UploadFile, BackgroundTasks
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from app.models.books import Books
from app.schemas.books import CreateBook, UpdateBook, ShowBook, ShowBookList
from app.utils.app_redis import get_redis


# Setup logger
logger = logging.getLogger(__name__)


class BookService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
        self.redis = get_redis()

    async def create_book(self, book_data: CreateBook):
        """
        Create a new book.

        Args:
            book_data (CreateBook): The data for the new book.

        Returns:
            ShowBook: The newly created book.

        Raises:
            HTTPException: If a book with the same title already exists.
            HTTPException: If there is an error creating the book.
        """
        check = self.db.query(Books).filter(Books.title == book_data.title).first()
        if check:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book with this title already exists")
        try:
            new_book = Books(
                title=book_data.title,
                author=book_data.author,
                price=book_data.price,
                publication_date=book_data.publication_date,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            self.db.add(new_book)
            self.db.commit()
            self.db.refresh(new_book)
            return ShowBook.model_validate(new_book)
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error creating book: {str(e)}"
            )

    async def update_book(self, book_id: str, book_data: UpdateBook):
        """
        Update a book by its ID with the provided data.

        Args:
            book_id (str): The ID of the book to update.
            book_data (UpdateBook): The data to update the book with.

        Raises:
            HTTPException: If the book with the given ID does not exist.
            HTTPException: If there is an error updating the book.

        Returns:
            ShowBook: The updated book.
        """
        book = self.db.query(Books).filter(Books.id == book_id).first()
        if not book:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
        try:
            book.title = book_data.title if book_data.title is not None and book_data.title != "" else book.title
            book.author = book_data.author if book_data.author is not None and book_data.author != "" else book.author
            book.price = book_data.price if book_data.price is not None and book_data.price != "" else book.price
            book.publication_date = (
                book_data.publication_date if book_data.publication_date is not None else book.publication_date
            )
            book.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(book)
            return ShowBook.model_validate(book)
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error updating book: {str(e)}"
            )

    async def get_book(self, book_id: str):
        """
        Get a book by its ID.

        Args:
            book_id (str): The ID of the book to retrieve.

        Raises:
            HTTPException: If the book with the given ID does not exist.

        Returns:
            ShowBook: The book with the given ID.
        """
        book = self.db.query(Books).filter(Books.id == book_id).first()
        if not book:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
        return ShowBook.model_validate(book)

    async def get_books(self, search: Annotated[str, None] = None, offset: int = 0, limit: int = 100):
        """
        Get books based on the given search query and pagination parameters.

        Args:
            search (str, optional): The search query to filter books by title or author. Defaults to None.
            offset (int, optional): The offset for pagination. Defaults to 0.
            limit (int, optional): The limit for pagination. Defaults to 100.

        Raises:
            HTTPException: If there is an error getting the books.

        Returns:
            ShowBookList: A list of books matching the search query, along with pagination metadata.
        """
        try:
            query = self.db.query(Books)
            if search:
                query = query.filter(Books.title.ilike(f"%{search}%") | Books.author.ilike(f"%{search}%"))
            # Get total count for pagination metadata
            total = query.count()

            # Applying pagination
            books = query.offset(offset).limit(limit).all()

            return ShowBookList(
                books=[ShowBook.model_validate(book) for book in books],
                total=total,
                offset=offset,
                limit=limit,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error getting books: {str(e)}"
            )

    async def delete_book(self, book_id: str):
        """
        Delete a book by its ID.

        Args:
            book_id (str): The ID of the book to delete.

        Raises:
            HTTPException: If the book with the given ID does not exist.
            HTTPException: If there is an error deleting the book.

        Returns:
            ShowBook: The book that was deleted.
        """
        book = self.db.query(Books).filter(Books.id == book_id).first()
        if not book:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
        try:
            old_book = ShowBook.model_validate(book)
            self.db.delete(book)
            self.db.commit()
            return old_book
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting book: {str(e)}"
            )

    async def process_csv_for_books(self, file_path: str, upload_id: str, user_id: str):
        """
        Process a CSV file for adding books.

        Args:
            file_path (str): The path to the CSV file.
            upload_id (str): The ID of the upload.
            user_id (str): The ID of the user.

        This function processes a CSV file for adding books to the database. It validates the CSV file,
        checks for duplicate titles, and stores the valid rows in the database. It also handles errors
        and stores the errors in Redis.
        """
        logger.info(
            f"Starting CSV file parsing for file: File path: {file_path}, upload_id: {upload_id}, User ID: {user_id})"
        )
        processed_rows = 0
        failed_rows = 0
        errors = []

        # Initialize status in Redis
        self.redis.set(f"upload:{upload_id}", json.dumps({"status": "pending", "errors": [], "user_id": user_id}))

        try:
            with open(file_path, newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                required_columns = {"title", "author", "price", "publication_date"}
                if not required_columns.issubset(reader.fieldnames):
                    error_msg = f"CSV missing required columns: {required_columns}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    return

                for row_number, row in enumerate(reader, start=1):
                    try:
                        # Validate and parse row
                        title = row["title"].strip()
                        if not title:
                            error_msg = f"Row {row_number}: Skipping row with empty title: {row}"
                            logger.warning(error_msg)
                            errors.append(error_msg)
                            failed_rows += 1
                            continue

                        # Check for duplicate title
                        if self.db.query(Books).filter(Books.title == title).first():
                            error_msg = f"Row {row_number}: Skipping duplicate title: {title}"
                            logger.warning(error_msg)
                            errors.append(error_msg)
                            failed_rows += 1
                            continue

                        # Parse price
                        try:
                            price = float(row["price"])
                            if price < 0:
                                raise ValueError("Price cannot be negative")
                        except ValueError as e:
                            error_msg = f"Row {row_number}: Skipping row with invalid price: {row} - {str(e)}"
                            logger.warning(error_msg)
                            errors.append(error_msg)
                            failed_rows += 1
                            continue

                        # Parse publication date
                        try:
                            publication_date = date.fromisoformat(row["publication_date"])
                        except ValueError as e:
                            error_msg = (
                                f"Row {row_number}: Skipping row with invalid publication_date: {row} - {str(e)}"
                            )
                            logger.warning(error_msg)
                            errors.append(error_msg)
                            failed_rows += 1
                            continue

                        # Store the book
                        new_book = Books(
                            title=title,
                            author=row["author"].strip(),
                            price=price,
                            publication_date=publication_date,
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc),
                        )
                        self.db.add(new_book)
                        processed_rows += 1
                        logger.debug(f"Row {row_number} processed successfully: {row}")
                    except Exception as e:
                        error_msg = f"Row {row_number}: Error processing row: {row} - {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        failed_rows += 1
                        continue
                self.db.commit()
                self.redis.set(
                    f"upload:{upload_id}", json.dumps({"status": "success", "errors": errors, "user_id": user_id})
                )
                logger.info(f"Completed CSV processing: {processed_rows} books added, {failed_rows} rows failed")
        except Exception as e:
            self.db.rollback()
            error_msg = f"Error processing CSV file {file_path} (Upload ID: {upload_id}): {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            self.redis.set(
                f"upload:{upload_id}", json.dumps({"status": "failed", "errors": errors, "user_id": user_id})
            )
        finally:
            # Clean up the temporary file
            try:
                os.remove(file_path)
                logger.debug(f"Deleted temporary file: {file_path}")
            except Exception as e:
                error_msg = f"Error deleting temporary file {file_path}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                self.redis.set(
                    f"upload:{upload_id}", json.dumps({"status": "failed", "errors": errors, "user_id": user_id})
                )

    async def upload_file_for_books_addition(self, file: UploadFile, background_tasks: BackgroundTasks, user_id: str):
        """
        Handle CSV file upload and schedule background task for processing.
        """
        # Validate file type
        if not file.filename.lower().endswith(".csv"):
            logger.warning(f"Invalid file type uploaded: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Only CSV files are allowed."
            )

        # Validate file size (e.g., max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            logger.warning(f"File too large: {file.filename}, size: {file.size} bytes")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large. Maximum size is 10MB.")

        try:
            # Generate unique upload ID
            upload_id = str(uuid.uuid4())
            # Save file temporarily
            file_path = self.upload_dir / f"{upload_id}_{file.filename}"
            with file_path.open("wb") as f:
                f.write(await file.read())
            logger.info(f"Uploaded file: {file.filename} (Upload ID: {upload_id})")
            self.redis.set(f"upload:{upload_id}", json.dumps({"status": "pending", "errors": [], "user_id": user_id}))

            # Schedule background task
            background_tasks.add_task(self.process_csv_for_books, str(file_path), upload_id, user_id)

            # Return immediate response
            return {"message": "CSV upload scheduled for processing", "filename": file.filename, "upload_id": upload_id}
        except Exception as e:
            logger.error(f"Error uploading file {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error uploading file: {str(e)}"
            )

    async def get_upload_status(self, upload_id: str, user_id: str):
        """
        Retrieve the upload status for a given upload ID and user ID.

        :param upload_id: The unique identifier of the upload.
        :type upload_id: str
        :param user_id: The unique identifier of the user.
        :type user_id: str
        :raises HTTPException: If the upload ID is not found or the user is not authorized to view the upload.
        :return: A dictionary containing the upload status, errors, and user ID.
        :rtype: dict
        """
        status_data = self.redis.get(f"upload:{upload_id}")
        if not status_data:
            logger.warning(f"Upload ID {upload_id} not found for User ID: {user_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found")
        status_dict = json.loads(status_data)
        if status_dict["user_id"] != user_id:
            logger.warning(f"User ID {user_id} not authorized to view Upload ID: {upload_id}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this upload")
        return status_dict
