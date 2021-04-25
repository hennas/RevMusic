
var USE_LASTFM = true;

function lastFMGet(href, handler) {
    /*
    Send a GET request to the requested LastFM API url. Handler then processes the response
    args:
        href: url to use
        handler: Function to use on the data
    */
    $.ajax({
        url: href,
        type: "GET",
        headers: {
            // Should use an identifiable User Agent
            // https://stackoverflow.com/questions/11278286/appropriate-user-agent-header-value
            'User-Agent': 'on_leguaani-TestApp/1.0',
        },
        success: handler,
        error: function(err) {
            alert("LastFM API calls are not working! Don't use this or check API key");
            USE_LASTFM = false;
            console.log(err);
        }
    });
}

function lastFMAlbumSearch(title) {
    /*
    Searches the LastFM API for an album with the given title. The info is then given to parseLastFMAlbumSearch()
    Call Documentation: https://www.last.fm/api/show/album.search
    args:
        title: Album title
    */
    if (!USE_LASTFM) return;
    var href = "http://ws.audioscrobbler.com/2.0/?method=album.search&album=" + title + "&api_key=" + api_keys.last_fm + "&format=json&limit=5";
    lastFMGet(href, parseLastFMAlbumSearch);
}

function parseLastFMAlbumSearch(data) {
    /*
    Extracts albums from LastFM Album.search response. The result is then rendered with renderLastFMAlbum
    args:
        data: LastFM response
    */
    data = data.results.albummatches.album;
    if (data == null) {
        $(".Album_Title").html(
            "<h4>No result for the LastFM search!</h4>"
        );
        return;
    }
    $(".Album_Title").html(
        "<h3>Result from LastFM:</h3></br>" 
    );
    $(".Album_Img").empty();
    $(".Album_Info").empty();
    let album = null;
    for (var i = 0; i < data.length; i++) {
        album = {
            "title": data[i].name,
            "artist": data[i].artist,
            "img_href": data[i].image[2]["#text"]
        }
        renderLastFMAlbum(album);
    }
}

function renderLastFMAlbum(album) {
    /*
    Renders the given albums info on screen. Info includes artist's name, album title and the album's cover art
    args:
        album: Dictionary with the albums info
    */
    if (album.img_href != "" && album.img_href != null) {
        $(".Album_Img").append(
            "<img class='album_img' src='" + album.img_href + "' />"
        );
    } else {
        $(".Album_Img").append(
            "<img class='album_img' src='/static/html/no_img.png' />"
        );
    }
    $(".Album_Info").append(
        "Title: " + album.title + "</br>" +
        "Artist: <a class='select_album_btn' onclick='lastFMArtistInfo(\"" + album.artist + "\")'>" + album.artist + "</a></br>" +
        "<button onclick='lastFMToDB(\""+album.title+"\",\""+album.artist+"\")'>Add to Database!</button></br>" +
        "----------------------------------------</br>"
    );
}

function lastFMToDB(title, artist) {
    /*
    Used to add LastFM search results to our database
    args:
        title: Album title
        artist: Artist's name
    */
    var new_album = {
        "unique_name": title.toLowerCase(),
        "title": title,
        "artist": artist
    }
    $.ajax({
        url: API_URL + ALBUMS_URL,
        type: "POST",
        data: JSON.stringify(new_album),
        contentType: PLAINJSON,
        success: function(data) {
            alert("Album " + title + " added!");
            renderAlbumSearch();
            getAlbums();
        },
        error: function(err) {
            if(err.responseText.indexOf("Already exists") != -1) {
                retryLastFMAdd(new_album);
            } else {
                errorAlert(err);
            }
        }
    });
}

function retryLastFMAdd(new_album) {
    /*
    Same as above, but trying a different unique name, since the lowercase title was already taken
    */
    new_album.unique_name = new_album.title.toLowerCase() + "_" + new_album.artist.toLowerCase();
    $.ajax({
        url: API_URL + ALBUMS_URL,
        type: "POST",
        data: JSON.stringify(new_album),
        contentType: PLAINJSON,
        success: function(data) {
            alert("Album " + title + " added!");
            renderAlbumSearch();
            getAlbums();
        },
        error: errorAlert
    });
}

function renderLastFMAlbumImg(title, artist, selected=false) {
    /*
    Call Documentation: https://www.last.fm/api/show/album.getInfo
    Renders album cover art obtained from LastFM. 
    args:
        title: Album title
        artist: Album's performer
        selected: Render a larger image, since only one album is currently selected (if true)
    */
    if (!USE_LASTFM) {
        $(".Album_Img").html("No LastFM");
        return;
    }
    // Return for await
    return $.ajax({
        url: "http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key="+api_keys.last_fm+"&artist="+artist+"&album="+title+"&format=json",
        type: "GET",
        headers: {
            'User-Agent': 'on_leguaani-TestApp/1.0',
        },
        success: function(data) {
            let img_class = "album_search_img";
            if (selected) {
                img_class = "album_img";
                $(".Album_Img").empty();
            }
            let img_href = '';
            try {
                img_href = data.album.image[2]["#text"];    
            } catch(err) {
                $(".Album_Img").append(
                    "<img class='" + img_class + "' src='/static/html/no_img.png' /></br>"
                );
                return;
            }
            if (img_href != null && img_href != "") {
                $(".Album_Img").append(
                    "<img class='" + img_class + "' src='" + img_href + "'/></br>"
                )
            } else {
                $(".Album_Img").append(
                    "<img class='" + img_class + "' src='/static/html/no_img.png' /></br>"
                );
            }
        },
        error: function (err) {
            alert("renderLastFMAlbumImg Failed!");
            USE_LASTFM = false;
            console.log(err);
        }
    });
}

function lastFMAlbumInfo(title, artist) {
    /*
    Call Documentation: https://www.last.fm/api/show/album.getInfo
    This is called when a specific album title and artist is searched
    args:
        title: Album title
        artist: Album's performer
    */
    if (!USE_LASTFM) return;
    var href = "http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key="+api_keys.last_fm+"&artist="+artist+"&album="+title+"&format=json";
    lastFMGet(href, parseLastFMAlbumInfo);
}

function parseLastFMAlbumInfo(data) {
    data = data.album;
    let album = {
        "title": data.name,
        "artist": data.artist,
        "img_href": data.image[2]["#text"]
    }
    $(".Album_Title").html(
        "<h3>Result from LastFM:</h3></br>" 
    );
    $(".Album_Img").empty();
    $(".Album_Info").empty();
    renderLastFMAlbum(album);
}

function lastFMArtistInfo(name) {
    /*
    This call obtains basic artist info from LastFM. Its then rendered
    args:
        name: Artist's name
    */
    var href = "http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist="+name+"&api_key="+api_keys.last_fm+"&format=json";
    lastFMGet(href, renderLastFMArtistInfo);
}

function renderLastFMArtistInfo(data) {
    // Popup based on: http://jsfiddle.net/gp54V/1/
    // Newline removal from: https://stackoverflow.com/questions/10805125/how-to-remove-all-line-breaks-from-a-string
    var artist = data.artist;
    if (artist == null) {
        alert("This artist was not found on LastFM");
        return;
    }
    $(".Artist_Info_Popup").html(
        "<div id='popupOverlay'></div>" +
        "<div id='artistPopupContent'>" +
            "<b>Artist:</b> " + artist.name + "</br>" +
            "<b>Bio:</b> " + artist.bio.summary.replace(/(\r\n|\n|\r)/gm, "") + "</br>" +
            "<b>Listeners:</b> " + artist.stats.listeners + "</br>" +
            "<b>Total Playcount:</b> " + artist.stats.playcount + "</br>" +
            "<img class='artist_img' src='" + artist.image[2]["#text"] + "'/></br>" +
            "<button class='close_artist_info_btn'>Close</button>" +
        "</div>"
    );
    $(".Artist_Info_Popup").fadeToggle();
    $(".close_artist_info_btn").on('click', function() {
        $(".Artist_Info_Popup").fadeToggle();
    });
}

function lastFMOthersListening() {
    /*
    Call documentation: https://www.last.fm/api/show/chart.getTopArtists
    */
    if (!USE_LASTFM) return;
    $.ajax({
        url: "http://ws.audioscrobbler.com/2.0/?method=chart.gettopartists&api_key="+api_keys.last_fm+"&format=json&limit=10",
        type: "get",
        headers: {
            'User-Agent': 'on_leguaani-TestApp/1.0',
        },
        success: function(data) {
            renderLastFMOthersListening(data.artists.artist);
        },
        error: function(err) {
            alert("LastFM API calls are not working! Don't use this or check API key");
            USE_LASTFM = false;
            console.log(err);
        }
    });
}

function renderLastFMOthersListening(artists) {
    $(".Listening_Title").html(
        "<h4>Top 10 Artists Normies are Listening to:</h4> (Based on LastFM) </br></br>"
    );
    $(".Listening_Info").empty();
    $(".Listening_Img").empty();
    for (var i = 0; i < artists.length; i++) {
        $(".Listening_Info").append(
            "\"Artist\": " + artists[i].name + "</br>" +
            "Listeners: " + artists[i].listeners + "</br>" +
            "----------------------------------------</br>"
        );
    }
}