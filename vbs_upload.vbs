strFilePath = "D:\idk\DFM\pyinstaller.txt"
url = "localhost:5500/sequence/post-file"
UploadFile strFilePath, strUplStatus, strUplResponse
MsgBox strUplStatus & vbCrLf & strUplResponse

Sub UploadFile(strPath, strStatus, strResponse)

    Dim strFile, strExt, strContentType, strBoundary, bytData, bytPayLoad

    On Error Resume Next
    With CreateObject("Scripting.FileSystemObject")
        If .FileExists(strPath) Then
            strFile = .GetFileName(strPath)
            strExt = .GetExtensionName(strPath)
        Else
            strStatus = "File not found"
            Exit Sub
        End IF
    End With
    With CreateObject("Scripting.Dictionary")
        .Add "php", "application/x-php"
        .Add "vbs", "application/x-vbs"
        .Add "jpe", "image/jpeg"
        .Add "jpg", "image/jpeg"
        .Add "jpeg", "image/jpeg"
        .Add "gif", "image/gif"
        .Add "png", "image/png"
        .Add "bmp", "image/bmp"
        .Add "ico", "image/x-icon"
        .Add "svg", "image/svg+xml"
        .Add "svgz", "image/svg+xml"
        .Add "tif", "image/tiff"
        .Add "tiff", "image/tiff"
        .Add "pct", "image/x-pict"
        .Add "psd", "image/vnd.adobe.photoshop"
        .Add "aac", "audio/x-aac"
        .Add "aif", "audio/x-aiff"
        .Add "flac", "audio/x-flac"
        .Add "m4a", "audio/x-m4a"
        .Add "m4b", "audio/x-m4b"
        .Add "mid", "audio/midi"
        .Add "midi", "audio/midi"
        .Add "mp3", "audio/mpeg"
        .Add "mpa", "audio/mpeg"
        .Add "mpc", "audio/x-musepack"
        .Add "oga", "audio/ogg"
        .Add "ogg", "audio/ogg"
        .Add "ra", "audio/vnd.rn-realaudio"
        .Add "ram", "audio/vnd.rn-realaudio"
        .Add "snd", "audio/x-snd"
        .Add "wav", "audio/x-wav"
        .Add "wma", "audio/x-ms-wma"
        .Add "avi", "video/x-msvideo"
        .Add "divx", "video/divx"
        .Add "flv", "video/x-flv"
        .Add "m4v", "video/mp4"
        .Add "mkv", "video/x-matroska"
        .Add "mov", "video/quicktime"
        .Add "mp4", "video/mp4"
        .Add "mpeg", "video/mpeg"
        .Add "mpg", "video/mpeg"
        .Add "ogm", "application/ogg"
        .Add "ogv", "video/ogg"
        .Add "rm", "application/vnd.rn-realmedia"
        .Add "rmvb", "application/vnd.rn-realmedia-vbr"
        .Add "smil", "application/x-smil"
        .Add "webm", "video/webm"
        .Add "wmv", "video/x-ms-wmv"
        .Add "xvid", "video/x-msvideo"
        .Add "js", "application/javascript"
        .Add "xml", "text/xml"
        .Add "html", "text/html"
        .Add "css", "text/css"
        .Add "txt", "text/plain"
        .Add "py", "text/x-python"
        .Add "pdf", "application/pdf"
        .Add "xhtml", "application/xhtml+xml"
        .Add "zip", "application/x-zip-compressed, application/zip"
        .Add "rar", "application/x-rar-compressed"
        .Add "cmd", "application/cmd"
        .Add "bat", "application/x-bat, application/x-msdos-program"
        .Add "exe", "application/exe, application/x-ms-dos-executable"
        .Add "msi", "application/x-msi"
        .Add "bin", "application/x-binary"
        .Add "crt", "application/x-x509-ca-cert"
        .Add "crl", "application/x-pkcs7-crl"
        .Add "pfx", "application/x-pkcs12"
        .Add "p12", "application/x-pkcs12"
        .Add "odc", "application/vnd.oasis.opendocument.chart"
        .Add "odf", "application/vnd.oasis.opendocument.formula"
        .Add "odb", "application/vnd.oasis.opendocument.database"
        .Add "odg", "application/vnd.oasis.opendocument.graphics"
        .Add "odi", "application/vnd.oasis.opendocument.image"
        .Add "odp", "application/vnd.oasis.opendocument.presentation"
        .Add "ods", "application/vnd.oasis.opendocument.spreadsheet"
        .Add "odt", "application/vnd.oasis.opendocument.tex"
        .Add "docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        .Add "dotx", "application/vnd.openxmlformats-officedocument.wordprocessingml.template"
        .Add "potx", "application/vnd.openxmlformats-officedocument.presentationml.template"
        .Add "ppsx", "application/vnd.openxmlformats-officedocument.presentationml.slideshow"
        .Add "pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        .Add "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        .Add "xltx", "application/vnd.openxmlformats-officedocument.spreadsheetml.template"
        .Add "ppam", "application/vnd.ms-powerpoint.addin.macroEnabled.12"
        .Add "ppa", "application/vnd.ms-powerpoint"
        .Add "potm", "application/vnd.ms-powerpoint.template.macroEnabled.12"
        .Add "ppsm", "application/vnd.ms-powerpoint.slideshow.macroEnabled.12"
        .Add "xlsm", "application/vnd.ms-excel.sheet.macroEnabled.12"
        .Add "pptm", "application/vnd.ms-powerpoint.presentation.macroEnabled.12"
        .Add "dotm", "application/vnd.ms-word.template.macroEnabled.12"
        .Add "docm", "application/vnd.ms-word.document.macroEnabled.12"
        .Add "doc", "application/msword"
        .Add "dot", "application/msword"
        .Add "pps", "application/mspowerpoint"
        .Add "ppt", "application/mspowerpoint,application/powerpoint,application/vnd.ms-powerpoint,application/x-mspowerpoint"
        .Add "xls", "application/vnd.ms-excel"
        .Add "xlt", "application/vnd.ms-excel"

        strContentType = .Item(LCase(strExt))
    End With
    If strContentType = "" Then
        strStatus = "Invalid file type"
        Exit Sub
    End If
    With CreateObject("ADODB.Stream")
        .Type = 1
        .Mode = 3
        .Open
        .LoadFromFile strPath
        If Err.Number <> 0 Then
            strStatus = Err.Description & " (" & Err.Number & ")"
            Exit Sub
        End If
        bytData = .Read
    End With
    strBoundary = String(6, "-") & Replace(Mid(CreateObject("Scriptlet.TypeLib").Guid, 2, 36), "-", "")
    With CreateObject("ADODB.Stream")
        .Mode = 3
        .Charset = "Windows-1252"
        .Open
        .Type = 2
        .WriteText "--" & strBoundary & vbCrLf
        .WriteText "Content-Disposition: form-data; name=""upload_file""; filename=""" & strFile & """" & vbCrLf
        .WriteText "Content-Type: """ & strContentType & """" & vbCrLf & vbCrLf
        .Position = 0
        .Type = 1
        .Position = .Size
        .Write bytData
        .Position = 0
        .Type = 2
        .Position = .Size
        .WriteText vbCrLf & "--" & strBoundary & "--"
        .Position = 0
        .Type = 1
        bytPayLoad = .Read
    End With
    With CreateObject("MSXML2.ServerXMLHTTP") 
        .SetTimeouts 0, 60000, 300000, 300000
        .Open "POST", "http://example.com/upload.php", False 
        .SetRequestHeader "Content-type", "multipart/form-data; boundary=" & strBoundary
        .Send bytPayLoad
        If Err.Number <> 0 Then
            strStatus = Err.Description & " (" & Err.Number & ")"
        Else
            strStatus = .StatusText & " (" & .Status & ")"
        End If
        If .Status = "200" Then strResponse = .ResponseText
    End With

End Sub