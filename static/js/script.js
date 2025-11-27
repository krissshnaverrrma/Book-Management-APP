async function searchGoogleBooks() {
	const query = document.getElementById("searchInput").value;
	const resultsArea = document.getElementById("resultsArea");
	const resultsGrid = document.getElementById("resultsGrid");

	if (!query) {
		alert("Please enter a book name!");
		return;
	}

	resultsArea.style.display = "block";
	resultsGrid.innerHTML = `
        <div class="col-12 text-center p-5">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-2 text-white">Searching...</p>
        </div>`;

	try {
		const response = await fetch(
			`https://www.googleapis.com/books/v1/volumes?q=${query}&maxResults=4`
		);
		const data = await response.json();

		resultsGrid.innerHTML = "";

		if (data.items) {
			data.items.forEach((book) => {
				const info = book.volumeInfo;
				const thumbnail = info.imageLinks
					? info.imageLinks.thumbnail
					: "https://via.placeholder.com/150";
				const category = info.categories
					? info.categories[0]
					: "General";

				const safeTitle = (info.title || "Unknown").replace(
					/'/g,
					"\\'"
				);
				const safeAuthor = (
					info.authors ? info.authors[0] : "Unknown"
				).replace(/'/g, "\\'");

				const card = `
                    <div class="col-md-3 mb-4">
                        <div class="book-card h-100 d-flex flex-column">
                            <img src="${thumbnail}" class="book-cover" alt="Cover">
                            <div class="card-body d-flex flex-column p-3">
                                <h6 class="fw-bold mb-1 text-truncate text-white" title="${info.title}">${info.title}</h6>
                                <p class="text-white-50 small mb-2 text-truncate">${safeAuthor}</p>
                                <span class="badge bg-light text-dark mb-3 align-self-start border">${category}</span>
                                <button onclick="addToLibrary('${safeTitle}', '${safeAuthor}', '${category}')" 
                                        class="btn btn-dark btn-sm mt-auto w-100">
                                    <i class="fas fa-plus me-1"></i> Add
                                </button>
                            </div>
                        </div>
                    </div>
                `;
				resultsGrid.innerHTML += card;
			});
		} else {
			resultsGrid.innerHTML =
				'<div class="col-12 text-center"><p class="text-white-50">No books found.</p></div>';
		}
	} catch (error) {
		console.error("Error fetching books:", error);
		resultsGrid.innerHTML =
			'<div class="col-12 text-center text-danger"><p>Error fetching books.</p></div>';
	}
}

async function addToLibrary(title, author, category) {
	try {
		const response = await fetch("/api/add", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ title, author, category }),
		});

		const result = await response.json();

		if (result.status === "success") {
			location.reload();
		} else {
			alert(result.message);
		}
	} catch (error) {
		console.error("Error adding book:", error);
	}
}

document.addEventListener("DOMContentLoaded", function () {
	const searchInput = document.getElementById("searchInput");
	if (searchInput) {
		searchInput.addEventListener("keypress", function (e) {
			if (e.key === "Enter") searchGoogleBooks();
		});
	}
});
