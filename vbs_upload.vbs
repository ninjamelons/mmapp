strFilePath = "D:\idk\DFM\67[0_5].txt"
url = "http://localhost:5500/sequence/post-sequence-file?seriesId=5"
UploadFile url, strFilePath, strUplStatus, strUplResponse
MsgBox strUplStatus & vbCrLf & strUplResponse

Sub UploadFile(url, strPath, strStatus, strResponse)

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
        .Add "txt", "text/plain"

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
        .WriteText "Content-Disposition: form-data; name=""file""; filename=""" & strFile & """" & vbCrLf
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
        .Open "POST", url, False 
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