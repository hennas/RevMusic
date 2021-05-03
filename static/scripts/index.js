"use strict";

// The API keys are read from config.js which is imported in the html file

const PLAINJSON = "application/json";

// The API lives here
const API_URL = "http://127.0.0.1:5000";
// Control names
const USERS_ALL = "revmusic:users-all";
const ALBUMS_ALL = "revmusic:albums-all";
const REVIEWS_ALL = "revmusic:reviews-all";
const REVIEWS_FOR_ALBUM = 'revmusic:reviews-for';
// API urls stored here
let USERS_URL = '';
let ALBUMS_URL = '';
let REVIEWS_URL = '';


function errorAlert(xhr) {
    /*
    Outputs the alerts produced by create_error_response
    */
    let msg = JSON.parse(xhr.responseText)['@error']['@message'];
    let msgs = JSON.parse(xhr.responseText)['@error']['@messages'][0];
    if (msgs == null) {
        alert(msg);
    } else {
        alert(msgs);
    }
}

window.onload = async function() {
    // Get the main API urls and render when the site is loaded
    lastFMOthersListening();
    getMainUrls();
    renderAddAlbum();
    renderAlbumSearch();
    renderReviewSearch();
    // Other renders in getMainUrls()
}

function getMainUrls() {
    /*
    Loads the URLs for revmusic:users-all, revmusic:albums-all, revmusic:reviews-all. After a successful GET, this calls rendering on URL dependent functions
    */
    $.ajax({
        url: API_URL + "/api/",
        success: function(data) {
            data = data["@controls"];
            USERS_URL = data[USERS_ALL]["href"];
            ALBUMS_URL = data[ALBUMS_ALL]["href"];
            REVIEWS_URL = data[REVIEWS_ALL]["href"].split("?")[0];
            // Render stuff dependent on the URLs
            getAlbums();
            renderNewestReviews();
        },
        error: function(xhr) {
            $("body").html("<h1>Couldn't connect to the API. Please check that the API_URL is correct and that the API is running!</h1>");
        }
    })
}

function renderAddAlbum() {
    /*
    This function renders a field that allows users to add albums to the database
    */
    $(".Add_Album").html(
        "<h3>Album not in our database?</h4>" + "<h4>Add it here:</h4>" +
        "Unique Name: <input type='text' id='add_unique_name' placeholder='title OR title_artist' required/></br>" +
        "Title: <input type='text' id='add_title' required/></br>" +
        "Artist: <input type='text' id='add_artist' required/></br>" +
        "Release Date: <input type='text' id='add_release' placeholder='2001-04-25'/></br>" +
        "Duration: <input type='text' id='add_duration' placeholder='01:44:36'/></br>" +
        "Genre: <input type='text' id='add_genre'/></br>" +
        "<button onclick='addAlbum()'>Submit!</button>"
    );
}

function renderAlbumSearch() {
    /*
    This function renders the album search field
    */
    $(".Album_Search").html(
        "<h3>Search for albums:</h3>" +
        "Title: <input id='title_field' type='text' value=''/></br>" +
        "Artist: <input id='artist_field' type='text' value=''/></br>" +
        "Unique Name: <input id='unique_name_field' type='text' value='' placeholder='title OR title_artist'/></br>" +
        "Genre: <input id='genre_field' type='text' value=''/></br>" +
        // lastFMSearch() defined in this file
        "<button onclick='getAlbums()'>Search RevMusic!</button>  |  <button onclick='lastFMSearch()'>Search LastFM!</button>" 
    );
}

function renderReviewSearch() {
    $(".Review_Search").html(
        "<h3>Search for reviews:</h3>" +
        "Filter By: <select id='filterby'>" +
            "<option value='album'>Album</option>" +
            "<option value='artist'>Artist</option>" +
            "<option value='genre'>Genre</option>" +
            "<option value='user'>User</option>" +
        "</select></br>" +
        "Searchword: <input type='text' id='searchword'/></br>" +
        "Timeframe: <input type='text' id='timeframe' placeholder='ddmmyyyy OR ddmmyyyy_ddmmyyyy'/></br>" +
        "Nlatest: <input type='number' id='nlatest' min='1' max='10' step='1' value='5'/></br>" +
        "<button onclick='searchReviews()'>Search!</button>" 
    );
}

function lastFMSearch() {
    let title = document.getElementById('title_field').value;
    let artist = document.getElementById('artist_field').value;
    if (title == "") {
        alert("Album Title required!");
        return;
    } else if(title != "" && artist != "") {
        lastFMAlbumInfo(title, artist)
    } else {
        lastFMAlbumSearch(title);
    }
}

function getAlbums() {
    /*
    Obtains all albums from RevMusic API. The albums are then filtered based on values in the Album Search field
    */
    $(".Album_Title").html("<h3>Albums:</h3>");
    $(".Album_Info").empty();
    $(".Album_Img").empty();
    let unique_name = document.getElementById('unique_name_field').value;
    let title = document.getElementById('title_field').value;
    let artist = document.getElementById('artist_field').value;
    let genre = document.getElementById('genre_field').value;
    $.ajax({
        url: API_URL + ALBUMS_URL,
        success: function(data) {
            var num_found = 0;
            data = data['items'];
            for(var i = 0; i < data.length; i++) {
                if(albumSelector(data[i], unique_name, title, artist, genre)) {
                    renderAlbum(data[i]);
                    num_found += 1;
                }
                // Lets not render too many to reduce amount of API calls
                if(num_found > 5) break;
            }
            if(num_found < 1) {
                $(".Album_Title").html('<h4>No albums found!</h4>');
            }
        },
        error: errorAlert
    });
}

function albumSelector(album, unique_name, title, artist, genre) {
    /*
    Checks if the given album matches search parameters
    */
    let matches = true;
    if(unique_name != "" && matches) {
        matches = unique_name == album.unique_name;
    }
    if(title != "" && matches) {
        matches = title == album.title;
    }
    if(artist != "" && matches) {
        matches = artist == album.artist;
    }
    if(genre != "" && matches) {
        matches = genre == album.genre;
    }
    return matches;
}

async function renderAlbum(album) {
    /*
    This function renders the basic info of the given album + some callable commands for the album
        album: All info of a certain album in json format
    */
    // This is awaited, so album cover arts appear in correct order. renderAlbumImg has return $.ajax()
    await renderLastFMAlbumImg(album.title, album.artist);
    $(".Album_Info").append(
        album.title  +
        " By <a class='select_album_btn' onclick='lastFMArtistInfo(\"" + album.artist + "\")'>" + album.artist + "</a></br>" +
        "==><a class='select_album_btn' onclick='renderSelectedAlbum(\"" + album["@controls"].self.href + "\")'>Show Info</a>   |   " +
        "<a class='select_album_btn' onclick='getAlbumReviews(\"" + album["@controls"].self.href + "\",\"" + album.title + "\")'>Show Reviews</a></br>" +
        "----------------------------------------</br>"
    );
}

function renderSelectedAlbum(href) {
    /*
    Called when user click "Show info" for an album. All info of the album is shown here. Commands for PUT and DELETE also included
    args:
        href: Link to the AlbumItem
    */
    $.ajax({
        url: API_URL + href,
        success: function(data) {
            $(".Album_Title").html("<h3>Album Info:</h3>");
            renderLastFMAlbumImg(data.title, data.artist, true);
            $(".Album_Info").html(
                "Title: " + data.title + "</br>" +
                "Artist: <a class='select_album_btn' onclick='lastFMArtistInfo(\"" + data.artist + "\")'>" + data.artist + "</a></br>" +
                "Released: " + data.release + "</br>" +
                "Duration: " + data.duration + "</br>" +
                "Genre: " + data.genre + "</br>" +
                "<button onclick='renderEditAlbum(\""+href+"\",\""+data.unique_name+"\",\""+data.title+"\",\""+data.artist+"\",\""+data.release+"\",\""+data.duration+"\",\""+data.genre+"\")'>Edit</button>" +
                "<button onclick='deleteAlbum(\""+href+"\")'>Delete</button>" +
                "<button onclick='renderReviewAlbum(\""+data["@controls"][REVIEWS_FOR_ALBUM].href+"\")'>Review</button>" +
                "<button onclick='getAlbums()'>Back</button>"
            );
        },
        error: errorAlert
    })
}

function renderEditAlbum(href, unique_name, title, artist, release, duration, genre) {
    /*
    This function renders an input field used to update an albums information
    */
    // Popup based on: http://jsfiddle.net/gp54V/1/
    console.log(release);
    if(release == "null") {
        release = '';
    }
    if(duration == "null") {
        duration = '';
    }
    if(genre == "null") {
        genre = '';
    }
    $(".Edit_Album_Popup").html(
        "<div id='popupOverlay'></div>" +
        "<div id='albumPopupContent'>" +
            //"Unique name: <input type='text' id='unique_name' name='unique_name' value='"+unique_name+"' /></br>" +
            "<input type='hidden' id='unique_name' value='" + unique_name + "'</p>" +
            "Title: <input type='text' id='title' name='title' value='"+title+"' /></br>" +
            "Artist: <input type='text' id='artist' name='artist' value='"+artist+"' /></br>" +
            "Release: <input type='text' id='release' name='release' value='"+release+"' /></br>" +
            "Duration: <input type='text' id='duration' name='duration' value='"+duration+"' /></br>" +
            "Genre: <input type='text' id='genre' name='genre' value='"+genre+"' /></br>" +
            "<button onclick='editAlbum(\""+href+"\")'>Submit</button>   |  " +
            "<button class='close_edit_album_btn'>Cancle</button>" +
        "</div>" 
    );
    $(".Edit_Album_Popup").fadeToggle();
    $(".close_edit_album_btn").on('click', function() {
        $(".Edit_Album_Popup").fadeToggle();
    });

}

function addAlbum() {
    // SOURCE: https://stackoverflow.com/questions/11704267/in-javascript-how-to-conditionally-add-a-member-to-an-object/38483660
    let release = document.getElementById("add_release").value;
    let duration = document.getElementById("add_duration").value;
    let genre = document.getElementById("add_genre").value;
    var new_album = {
        "unique_name": document.getElementById("add_unique_name").value,
        "title": document.getElementById("add_title").value,
        "artist": document.getElementById("add_artist").value,
        ...(release != "") && {'release': release},
        ...(duration != "") && {'duration': duration},
        ...(genre != "") && {'genre': genre},
    };
    $.ajax({
        url: API_URL + ALBUMS_URL,
        type: "POST",
        data: JSON.stringify(new_album),
        contentType: PLAINJSON,
        success: function(data) {
            alert("Album " + document.getElementById("add_title").value + " added!");
            renderAddAlbum();
            getAlbums();
        },
        error: errorAlert
    });
}

function editAlbum(href) {
    /*
    Reads the album input field and sends the data with PUT to RevMusic. On success, alert shown to user and album info on the page is updated
    args:
        href: Link to the AlbumItem
    // SOURCE: https://stackoverflow.com/questions/11704267/in-javascript-how-to-conditionally-add-a-member-to-an-object/38483660
    */
    let release = document.getElementById("release").value;
    let duration = document.getElementById("duration").value;
    let genre = document.getElementById("genre").value;
    var updated_album = {
        'unique_name': document.getElementById('unique_name').value,
        'title': document.getElementById('title').value,
        'artist': document.getElementById('artist').value,
        ...(release != "") && {'release': release},
        ...(duration != "") && {'duration': duration},
        ...(genre != "") && {'genre': genre},
    };
    $.ajax({
        url: API_URL + href,
        type: "PUT",
        data: JSON.stringify(updated_album),
        dataType: "text",
        contentType: PLAINJSON,
        success: function(data) {
            alert('Album info updated');
            $(".Edit_Album_Popup").fadeToggle();
            renderSelectedAlbum(href);
        },
        error: errorAlert
    });
}

function deleteAlbum(href) {
    /*
    Used to delete the specified album from the database
    args:
        href: Link to the AlbumItem
    */
    if (confirm('Are you sure you want to delete this album?')) {
        $.ajax({
            url: API_URL + href,
            type: "DELETE",
            success: function() {
                alert("Album deleted!");
                getAlbums();
            },
            error: errorAlert
        });
    }
}

function renderNewestReviews() {
    /*
    Renders 5 newest reviews. Called when the site is loaded
    */
    $(".Reviews").html("<h3>Newest Reviews:</h3>");
    $.ajax({
        url: API_URL + REVIEWS_URL + "?nlatest=5",
        success: function(data) {
            data = data["items"];
            for(var i = 0; i < data.length; i++) {
                renderReview(data[i]);
            }
        },
        error: function(data) {}
    });
}

function renderReviewAlbum(href) {
    $(".Add_Review_Popup").html(
        "<div id='popupOverlay'></div>" +
        "<div id='reviewPopupContent'>" +
            "User: <input type='text' id='add_review_user' name='add_review_user'/></br>" +
            "Title: <input type='text' id='add_review_title' name='add_review_title'/></br>" +
            "Content: <input type='text' id='add_review_content' name='add_review_content'/></br>" +
            "Star Rating: <input type='number' id='add_review_star_rating' min='1' max='5' step='1' value='3'/>" +
            "<button onclick='addReview(\""+href+"\")'>Submit</button>   |  " +
            "<button class='close_add_review_btn'>Cancle</button>" +
        "</div>"
    );
    $(".Add_Review_Popup").fadeToggle();
    $(".close_add_review_btn").on('click', function() {
        $(".Add_Review_Popup").fadeToggle();
    });
}

function addReview(href) {
    var new_review = {
        'user': document.getElementById('add_review_user').value,
        'title': document.getElementById('add_review_title').value,
        'content': document.getElementById('add_review_content').value,
        'star_rating': parseInt(document.getElementById('add_review_star_rating').value), // TODO: ERROR HANDLING
    };
    $.ajax({
        url: API_URL + href, // TODO: FIX THIS URL
        type: "POST",
        data: JSON.stringify(new_review),
        dataType: "text",
        contentType: "application/json",
        processData: false,
        success: function(data) {
            alert('New review added!');
            $(".Add_Review_Popup").fadeToggle();
            //renderSelectedAlbum(href);
            renderNewestReviews();
        },
        error: errorAlert
    });
}

function getAlbumReviews(href, title) {
    /*
    Loads the given album object and obtains its reviews for rendering
    args:
        href: Link to album item
        title: Title of the album
    */
    $.ajax({
        url: API_URL + href,
        success: function(data) {
            $.ajax({
                url: API_URL + data["@controls"][REVIEWS_FOR_ALBUM].href,
                success: function (data) {
                    $(".Reviews").html(
                        "<h3>Newest reviews for: " + title + "</h3>"
                    );
                    for(var i = 0; i < data["items"].length; i++) {
                        renderFullReview(data["items"][i]["@controls"].self.href);
                    }
                },
                error: errorAlert
            });
        },
        error: errorAlert
    });
}

function renderReview(review) {
    /*
    Renders basic info of a given review
    args:
        review: All info of a review as JSON
    */
    $(".Reviews").append(
        review.user + " reviewed " + review.album + "</br>" +
        "They gave the album " + review.star_rating + " star</br>" +
        "<a class='select_album_btn' onclick='renderFullReview(\"" + review["@controls"].self.href + "\",\"" + true + "\")'>Show full review</a></br>" +
        "----------------------------------------</br>"
    );
}

function renderFullReview(href, clear_reviews=false) {
    $.ajax({
        url: API_URL + href,
        success: function(review) {
            if(clear_reviews) {
                $(".Reviews").empty();
            }
            $(".Reviews").append(
                "<b>Title:</b> " + review.title + "</br>" +
                "<b>By:</b> " + review.user + "</br>" +
                "<b>Content:</b></br>" + review.content + "</br>" +
                "<b>Star Rating:</b> " + review.star_rating + "</br>" +
                "----------------------------------------</br>"
            );
            if(clear_reviews) {
                $(".Reviews").append(
                    "<button onclick='renderNewestReviews()'>Back</button>"
                );
            }
        },
        error: errorAlert
    });
}

function searchReviews() {
    let searchword = document.getElementById('searchword').value;
    let timeframe = document.getElementById('timeframe').value;
    let nlatest = parseInt(document.getElementById('nlatest').value);
    // SOURCE: https://stackoverflow.com/questions/11704267/in-javascript-how-to-conditionally-add-a-member-to-an-object/38483660
    var search_params = {
        'filterby': document.getElementById('filterby').value,
        ...(searchword != "") && {'searchword': searchword},
        ...(timeframe != "") && {'timeframe': timeframe},
        ...(nlatest != null) && {'nlatest': nlatest},
    };
    $.ajax({
        url: API_URL + REVIEWS_URL,
        data: jQuery.param(search_params),
        success: function(data) {
            $(".Reviews").html("<h3>Reviews:</h3>");
            for(var i = 0; i < data.items.length; i++) {
                renderReview(data.items[i]);
            }
        },
        error: errorAlert
    });
}
