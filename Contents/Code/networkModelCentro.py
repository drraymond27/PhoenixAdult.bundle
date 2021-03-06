import PAsearchSites
import PAutils

query = 'content.load?_method=content.load&tz=1&limit=512&transitParameters[v1]=OhUOlmasXD&transitParameters[v2]=OhUOlmasXD&transitParameters[preset]=videos'
updatequery = 'content.load?_method=content.load&tz=1&filter[id][fields][0]=id&filter[id][values][0]={}&limit=1&transitParameters[v1]=ykYa8ALmUD&transitParameters[preset]=scene'
modelquery = 'model.getModelContent?_method=model.getModelContent&tz=1&limit=25&transitParameters[contentId]='

# for future use:
aboutquery = 'Client_Aboutme.getData?_method=Client_Aboutme.getData'


def getAPIURL(url):
    req = PAutils.HTTPRequest(url)

    if req.text:
        ah = re.search(r'"ah".?:.?\"([0-9a-zA-Z\(\)\@\:\,\/\!\+\-\.\$\_\=\\\']*)\"', req.text).group(1)[::-1] + '/'
        aet = re.search(r'"aet".?:([0-9]*)', req.text).group(1) + '/'
        Log(ah + aet)
        return ah + aet
    return None


def getJSONfromAPI(url):
    req = PAutils.HTTPRequest(url)

    if req.text:
        return json.loads(req.text).get('response').get('collection')
    return None


def search(results, lang, siteNum, searchData):
    apiurl = getAPIURL(PAsearchSites.getSearchBaseURL(siteNum) + '/videos/')
    searchResults = getJSONfromAPI(PAsearchSites.getSearchSearchURL(siteNum) + apiurl + query)

    if searchResults:
        for searchResult in searchResults:
            sceneID = str(searchResult['id'])
            releaseDate = parse(searchResult.get('sites').get('collection').get(sceneID).get('publishDate')).strftime('%Y-%m-%d')

            if searchData.date:
                delta = abs(parse(searchData.date) - parse(releaseDate))
                if delta.days < 2:
                    artobj = PAutils.Encode(json.dumps(searchResult.get('_resources').get('base')))
                    titleNoFormatting = str(searchResult['title'])
                    score = 100 - Util.LevenshteinDistance(searchData.date, releaseDate)
                    results.Append(MetadataSearchResult(id='%s|%d|%s|%s' % (sceneID, siteNum, titleNoFormatting, artobj),
                                                        name='%s %s [%s]' % (titleNoFormatting, releaseDate, PAsearchSites.getSearchSiteName(siteNum)),
                                                        score=score, lang=lang))
            else:
                titleNoFormatting = str(searchResult['title'])
                score = 100 - Util.LevenshteinDistance(searchData.title.lower(), titleNoFormatting.lower())

                if score >= 90:
                    artobj = PAutils.Encode(json.dumps(searchResult.get('_resources').get('base')))
                    results.Append(MetadataSearchResult(id='%s|%d|%s|%s' % (sceneID, siteNum, titleNoFormatting, artobj), name='%s %s [%s]' % (titleNoFormatting, releaseDate, PAsearchSites.getSearchSiteName(siteNum)), score=score, lang=lang))

    return results


def update(metadata, siteNum, movieGenres, movieActors):
    metadata_id = str(metadata.id).split('|')
    sceneID = metadata_id[0]
    title = metadata_id[2].strip()
    apiurl = getAPIURL(PAsearchSites.getSearchBaseURL(siteNum) + '/scene/' + sceneID + '/' + title)
    apiurl = PAsearchSites.getSearchSearchURL(siteNum) + apiurl
    searchResult = getJSONfromAPI(apiurl + updatequery.format(sceneID))[0]

    # Title
    metadata.title = searchResult['title']

    # Summary
    metadata.summary = searchResult['description']

    # Studio
    metadata.studio = PAsearchSites.getSearchSiteName(siteNum)

    # Tagline and Collection(s)
    metadata.collections.clear()
    metadata.collections.add(metadata.studio)

    # Release Date
    date_object = parse(searchResult.get('sites').get('collection').get(sceneID).get('publishDate'))
    metadata.originally_available_at = date_object
    metadata.year = metadata.originally_available_at.year

    # Genres
    movieGenres.clearGenres()
    movieActors.clearActors()

    if 'tags' in searchResult:
        genres = searchResult['tags'].get('collection')

        if type(genres) is not list:
            for (key, value) in genres.items():
                genre = value.get('alias')

                if genre:
                    if siteNum == 1027:
                        genre = genre.replace('-', ' ')
                        movieActors.addActor(genre, '')
                    else:
                        movieGenres.addGenre(genre)

    # Actors
    actors = getJSONfromAPI(apiurl + modelquery + sceneID)

    if type(actors) is not list:
        for (key, value) in actors.items():
            collect = value.get('modelId').get('collection')

            for (k, val) in collect.items():
                actorName = val.get('stageName')

                if actorName:
                    movieActors.addActor(actorName, '')

    if siteNum == 1024:
        baseactor = 'Aletta Ocean'
    elif siteNum == 1025:
        baseactor = 'Eva Lovia'
    elif siteNum == 1026:
        baseactor = 'Romi Rain'
    elif siteNum == 1030:
        baseactor = 'Dani Daniels'
    elif siteNum == 1031:
        baseactor = 'Chloe Toy'
    elif siteNum == 1033:
        baseactor = 'Katya Clover'
    elif siteNum == 1035:
        baseactor = 'Lisey Sweet'
    elif siteNum == 1037:
        baseactor = 'Gina Gerson'
    elif siteNum == 1038:
        baseactor = 'Valentina Nappi'
    elif siteNum == 1039:
        baseactor = 'Vina Sky'
    elif siteNum == 1058:
        baseactor = 'Vicki Valkyrie'
    elif siteNum == 1075:
        baseactor = 'Dillion Harper'
    else:
        baseactor = ''

    movieActors.addActor(baseactor, '')

    # Posters
    art = []
    artobj = json.loads(PAutils.Decode(metadata_id[3]))

    if artobj:
        for searchResult in artobj:
            art.append(searchResult.get('url'))

    Log('Artwork found: %d' % len(art))
    for idx, posterUrl in enumerate(art, 1):
        if not PAsearchSites.posterAlreadyExists(posterUrl, metadata):
            # Download image file for analysis
            try:
                image = PAutils.HTTPRequest(posterUrl)
                im = StringIO(image.content)
                resized_image = Image.open(im)
                width, height = resized_image.size
                # Add the image proxy items to the collection
                if width > 1 or height > width:
                    # Item is a poster
                    metadata.posters[posterUrl] = Proxy.Media(image.content, sort_order=idx)
                if width > 100 and width > height and idx > 1:
                    # Item is an art item
                    metadata.art[posterUrl] = Proxy.Media(image.content, sort_order=idx)
            except:
                pass

    return metadata
