import json
import os
from html import unescape
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from .models import Book, BookImage

def index(request):
    if request.method == "GET":
         return render(request, "books/index.html")
    else:
          # For none get requests
          return HttpResponseBadRequest("Invalid request method")
         
def add_book(request):
        if request.method == "GET":       
             # Get categories
             categories = sorted(set(Book.objects.values_list("category", flat=True)))
             return render(request, "books/addbook.html", {
                    "categories": categories
             })
        else:
          # For none get requests
          return HttpResponseBadRequest("Invalid request method")
   
def save_book(request):
     # Check it's post
     if request.method == "POST":
          # Get book data from form
          book_data = {
               "bookid": request.POST["book-id"],
               "isbn_10": request.POST["book-isbn-10"],
               "isbn_13": request.POST["book-isbn-13"],
               "title": request.POST["book-title"],
               "language": request.POST["book-language"],
               "subtitle": request.POST["book-subtitles"],
               "authors": request.POST["book-authors"],
               "publisher": request.POST["book-publisher"],
               "category": request.POST.get("book-category", None),
               "published_date": request.POST["book-publication-date"],
               "page_count": request.POST["book-page-count"],
               "height": request.POST["book-height"],
               "width": request.POST["book-width"],
               "thickness": request.POST["book-thickness"],
               "print_type": request.POST["book-print-type"],
               "dust_jacket": request.POST.get("book-dust-jacket", None),
               "description": request.POST["book-description"],
               "binding": request.POST.get("book-binding", None),
               "condition": request.POST.get("book-condition", None),
          }

          # Extract id if present
          id = request.POST.get("id")
          if id is not None:          
               # Book instance already exists
               book = Book.objects.get(id=id)

               # Convert saved data to dict for comparison
               old_book_data = model_to_dict(book)

               if old_book_data != book_data:
                    # Update where necessary
                    for key, value in book_data.items():
                         setattr(book, key, value)
                         book.save()
               
               # Check for new images
               image_keys = [key for key in request.FILES.keys() if key.startswith("image_")]

               if len(image_keys) > 0:
                    # Loop over and save images
                    for key in image_keys:
                         image = request.FILES[key]
                         book_image = BookImage(image=image, book=book)
                         book_image.save()
               
               # Get id          
               id = book.id
               return JsonResponse({"message": "Book updated successfully", "id": id})
               
          else:
               # Make new book and save
               book = Book(**book_data)
               book.save()

               # Extract images
               image_keys = [key for key in request.FILES.keys() if key.startswith("image_")]

               # Loop over and save images
               for key in image_keys:
                    image = request.FILES[key]
                    book_image = BookImage(image=image, book=book)
                    book_image.save()

               # Get associated images
               images = BookImage.objects.filter(book=book)

               # Get the just added book
               book = Book.objects.get(id=book.id)
               book.images.set(images)
               book.save()

               id = book.id
               return JsonResponse({"message": "Book saved successfully", "id": id})
     else:
          # For none post requests
          return HttpResponseBadRequest("Invalid request method")

def delete_book(request):
     if request.method == "POST":
          # Extract id
          id = request.body.decode('utf-8')
          
          # Get book
          book = Book.objects.get(id=id)

          # Delete book
          book.delete()

          return JsonResponse({"message": "Book deleted", "id": id})
     else:
          # For none post requests
          return HttpResponseBadRequest("Invalid request method")

def edit_book(request, id):
     if request.method == "GET":
          # Get book
          book = Book.objects.get(id=id)

          # Get categories
          categories = sorted(set(Book.objects.values_list("category", flat=True)))

          return render(request, "books/editbook.html" , {
               "book": book,
               "categories": categories
          })
     else:
          # For none get requests
          return HttpResponseBadRequest("Invalid request method")

def book(request, id):
     if request.method == "GET":
          # Get book object
          book = Book.objects.get(id=id)

          # Get images
          images = list(book.images.values_list('image', flat=True))
          first_image = images.pop(0)

          return render(request, "books/book.html", {
               "book": book,
               "first_image": first_image,
               "images": images
          })
     else:
          # For none get requests
          return HttpResponseBadRequest("Invalid request method")

def get_api_key(request):
    if request.method == "GET":
          google_api_key = os.environ.get("GOOGLE_BOOKS_API_KEY")
          return JsonResponse({"google_api_key": google_api_key})
    else:
          # For none get requests
          return HttpResponseBadRequest("Invalid request method")

def inventory(request):
    if request.method == "GET":
          # Get all books and categories
          books = Book.objects.all()
          categories = sorted(set(Book.objects.values_list("category", flat=True)))
          conditions = sorted(set(Book.objects.values_list("condition", flat=True)))
          return render(request,"books/inventory.html", {
               "books": books,
               "categories": categories,
               "conditions": conditions
          })
    else:
         # For none get requests
         return HttpResponseBadRequest("Invalid request method")

def get_images(request, id):
      if request.method == "GET":
          # Get book
          book = Book.objects.get(id=id)

          # Get associated images
          bookImages = BookImage.objects.filter(book=book)
          images = []
          for image in bookImages:
               data = {
                    'image': unescape(image.image.url)
               }
               images.append(data)
          return JsonResponse({"images": images})
      else:
          # For none get requests
          return HttpResponseBadRequest("Invalid request method")