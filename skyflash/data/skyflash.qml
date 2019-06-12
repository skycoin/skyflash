import QtQuick 2.9
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.0
import QtQuick.Dialogs 1.1

ApplicationWindow {
    id: windows
    width: 398
    visible: true
    title: qsTr("Skyflash tool")

    // about dialog
    MessageDialog {
        id: aboutDiag
        title: "About Skyflash"
        Text {
            textFormat: Text.RichText
            onLinkActivated: Qt.openUrlExternally(link)
            padding: 10
            text: "<p><a href='http://github.com/skycoin/skyflash'>Skyflash</a> is the official tool to configure, build and flash the Skyminer images based on <a href='http://github.com/skycoin/skybian'>Skybian</a>.<br></p><p>Current version: v0.0.4-beta</p>"

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton
                cursorShape: parent.hoveredLink ? Qt.PointingHandCursor : Qt.ArrowCursor
            }
        }
        onAccepted: visible = false
    }

    // generic warning dialog
    MessageDialog {
        id: warnDiag
        icon: StandardIcon.Warning
        title: ""
        text: ""
        onAccepted: {
            warnDiag.visible = false
        }
    }

    // generic warning dialog
    MessageDialog {
        id: errorDiag
        icon: StandardIcon.Critical
        title: ""
        text: ""
        onAccepted: {
            errorDiag.visible = false
        }
    }

    // generic Success/Info dialog
    MessageDialog {
        id: okDiag
        icon: StandardIcon.Information
        title: ""
        text: ""
        onAccepted: {
            errorDiag.visible = false
        }
    }

    FileDialog {
        id: fileDialog
        title: "Please choose a file"
        folder: shortcuts.home
        nameFilters: ["Supported Files (*.tar *.tar.gz *.tar.xz *.img)"]
        selectMultiple: false

        onAccepted: {
            skf.localFile(fileDialog.fileUrls)
        }

        onRejected: {
            sbText.text = "You declined to choose a file."
        }
    }

    menuBar: MenuBar {
        Menu {
            title: "&File"

            MenuItem {
                text: "E&xit"
                shortcut: StandardKey.Quit
                onTriggered: Qt.quit()
            }
        }

        Menu {
            title: "&Help"

            MenuItem {
                text: "User's Manual"
                onTriggered: skf.openManual()
            }

            MenuItem {
                text: "About."
                onTriggered: aboutDiag.open()
            }
        }
    }

    // main placeholder
    ColumnLayout {
        id: mainBox
        anchors.rightMargin: 4
        anchors.leftMargin: 4
        anchors.bottomMargin: 4
        anchors.topMargin: 4
        anchors.fill: parent
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: false
        visible: true

        // image box
        ColumnLayout {
            id: boxImage
            transformOrigin: Item.TopLeft
            Layout.fillHeight: true
            Layout.alignment: Qt.AlignLeft | Qt.AlignTop
            spacing: 10
            visible: true
            Layout.fillWidth: true

            // box title
            Rectangle {
                Layout.fillWidth: true
                width: parent.width
                height: 22
                color: "lightblue"
                radius: 3

                Label {
                    text: "1. Download or browse a local Skybian release file:"
                    font.pixelSize: 14
                    font.bold: true
                    color: "black"
                }
            }

            // buttons
            RowLayout {
                RowLayout {
                    id: phDownloadButtons
                    
                    // Download button
                    Button {
                        id: btDown
                        Layout.preferredHeight: 30
                        Layout.preferredWidth: 80
                        text: "Download"
                        tooltip: "Click here to download the base Skybian image from the official site"

                        onClicked: {
                            skf.downloadSkybian()
                            btDown.text = "Cancel"
                            btDown.tooltip = "Click here to cancel the download"
                        }
                    }

                    // Browse button
                    Button {
                        id: btBrowse
                        Layout.preferredHeight: 30
                        Layout.preferredWidth: 80
                        text: "Browse"
                        tooltip: "Click here to browse for an already downloaded Skybian release file"

                        onClicked: { fileDialog.open() }
                    }
                }

                // label
                Label {
                    id: lbImageComment
                    Layout.fillWidth: true
                    text: ""
                }
            }

            // download ProgressBar
            ProgressBar {
                id: pbDownload
                Layout.fillWidth: true
                visible: false
                maximumValue: 100
                minimumValue: 0
                value: 0.1
            }
        }

        // network box
        ColumnLayout {
            id: boxNetwork
            spacing: 10
            visible: false

            // box title
            Rectangle {
                Layout.fillWidth: true
                width: parent.width
                height: 22
                color: "lightblue"
                radius: 3

                Label {
                    text: "2. Configure the network settings."
                    font.pixelSize: 14
                    font.bold: true
                    color: "black"
                }
            }

            // defaults CheckBox
            CheckBox {
                id: ckbDefaultNetwork
                text: "Use the Skyminer's defaults"
                checked: true

                onCheckedChanged: {
                    if (ckbDefaultNetwork.checked == true) {
                        // set default values
                        txtGateway.text = "192.168.0.1"
                        txtDNS.text = "1.0.0.1, 1.1.1.1"
                        txtManager.text = "192.168.0.2"
                        txtNodes.text = "7"
                        // disabling the input on the fields
                        txtGateway.enabled = false
                        txtDNS.enabled = false
                        txtManager.enabled = false
                        txtNodes.enabled = false
                        // net details are not shown
                        networkDetails.visible = false
                    } else {
                        // enable the fields for edit
                        txtGateway.enabled = true
                        txtDNS.enabled = true
                        txtManager.enabled = true
                        txtNodes.enabled = true
                        // net details are shown
                        networkDetails.visible = true
                    }

                    // if you change the config of the network and the
                    // build button is disables, you must enable it
                    if (btBuild.enabled == false) {
                        btBuild.enabled = true
                    }
                }
            }

            // gateway
            GridLayout {
                columns: 2
                rows: 4
                id: networkDetails
                visible: false

                // gateway
                Label { text: "Network gateway:" }

                TextField {
                    id: txtGateway
                    Layout.preferredWidth: 200
                    placeholderText: "192.168.0.1"
                    text: "192.168.0.1"
                    maximumLength: 16
                    enabled: false
                    inputMask: "000.000.000.000; "
                    // ToolTip.text: "This is the network Gateway IP"
                }

                // dns
                Label { text: "Network DNS:" }

                TextField  {
                    id: txtDNS
                    Layout.preferredWidth: 200
                    placeholderText: "1.0.0.1, 1.1.1.1"
                    text: "1.0.0.1, 1.1.1.1"
                    maximumLength: 34
                    enabled: false
                    inputMask: "000.000.000.000, 000.000.000.000; "
                    // ToolTip.text: "This is DNS your nodes will use to resolve names on the net"
                }

                // manager IP
                Label { text: "Manager IP:" }

                TextField {
                    id: txtManager
                    Layout.preferredWidth: 200
                    placeholderText: "192.168.0.2"
                    text: "192.168.0.2"
                    maximumLength: 16
                    enabled: false
                    inputMask: "000.000.000.000; "
                    // ToolTip.text: "This is the IP of the manager node"
                }

                // node count
                Label { text: "Node count:" }

                TextField  {
                    id: txtNodes
                    Layout.preferredWidth: 200
                    placeholderText: "7"
                    text: "7"
                    maximumLength: 5
                    enabled: false
                    inputMask: "000"
                    // ToolTip.text: "How many nodes we must build images for, not counting the manager node"
                }
            }
        }

        // build box
        ColumnLayout {
            id: boxBuild
            spacing: 10
            visible: false

            // box title
            Rectangle {
                Layout.fillWidth: true
                width: parent.width
                height: 22
                color: "lightblue"
                radius: 3

                Label {
                    text: "3. Build your custom images."
                    font.pixelSize: 14
                    font.bold: true
                    color: "black"
                }
            }

            RowLayout {
            // build button
                Button {
                    id: btBuild
                    text: "Build the images "

                    onClicked: {
                        // call skyflash to build the images
                        skf.imagesBuild(txtGateway.text, txtDNS.text, txtManager.text, txtNodes.text)
                    }
                }

                Label {
                    id: lbBuild
                    text: ""
                }
            }

            // image progress bars
            ColumnLayout {
                id: buildProgressBars
                visible: false

                // particular image progress
                RowLayout{
                    Label {
                        text: "Single image:"
                        color: "black"
                    }
                    ProgressBar {
                        id: pbBuildSingle
                        Layout.fillWidth: true
                        visible: true
                        maximumValue: 100
                        minimumValue: 0
                        value: 0
                    }
                }

                // overall progress
                RowLayout{
                    Label {
                        text: "Overall:"
                        color: "black"
                    }
                    ProgressBar {
                        id: pbBuildOverall
                        Layout.fillWidth: true
                        visible: true
                        maximumValue: 100
                        minimumValue: 0
                        value: 0
                    }
                }
            }
        }

        // flash box
        ColumnLayout {
            id: boxFlash
            spacing: 10
            visible: false

            // box title
            Rectangle {
                Layout.fillWidth: true
                width: parent.width
                height: 22
                color: "lightblue"
                radius: 3

                Label {
                    text: "4. Flash the images [Optional see User Manual]"
                    font.pixelSize: 14
                    font.bold: true
                    color: "black"
                }
            }

            // flash tools
            RowLayout {
                // pick your uSD device
                Label {
                    id: lbSdCard
                    text: "Device to flash:"
                }

                // ComboBox uSD
                ComboBox {
                    id: cbSdCard
                    currentIndex: 0
                    model: skf.cards
                    Layout.preferredHeight: 30
                    Layout.preferredWidth: 200

                    onCurrentTextChanged: {
                        if (currentText != "Please insert a card") {
                            skf.selectedCard = currentText
                            btFlash.enabled = true
                        } else {
                            skf.selectedCard = ""
                            btFlash.enabled = false
                        }
                        // call to update the selected text
                        skf.pickCard(currentText)
                    }
                }
            }

            // image to flash
            RowLayout {
                // pick your uSD
                Label {
                    id: lbImage2Flash
                    text: "Image to flash: "
                }

                // ComboBox uSD
                ComboBox {
                    id: cbImage2flash
                    currentIndex: 0
                    model: skf.images2flash
                    Layout.preferredHeight: 30
                    Layout.preferredWidth: 200
                    onCurrentTextChanged: {
                        // call to update the selected text
                        skf.pickimages2flash(currentText)
                    }
                }
            }

            // Flash Button, alone in a row
            RowLayout {
                // Start Flashing!
                Button {
                    id: btFlash
                    Layout.preferredHeight: 30
                    Layout.preferredWidth: 120
                    enabled: false
                    text: "Start Flashing"
                    tooltip: "Click here to start flashing the cards with the built images"

                    onClicked: {
                        // call skyflash to flash the images and show the progress
                        flashProgressBox.visible = true
                        skf.imageFlash()
                    }
                }

                // Please Review
                Label {
                    id: lbPleaseReview
                    text: " Please double check before start!"
                    color: "red"
                }
            }

            // box
            ColumnLayout {
                id: flashProgressBox
                visible: false

                // flash ProgressBar
                RowLayout{
                    Label {
                        text: "Single Image:"
                        color: "black"
                    }
                    ProgressBar {
                        id: pbFlash
                        Layout.fillWidth: true
                        visible: true
                        maximumValue: 100
                        minimumValue: 0
                        value: 0
                    }
                }
            }
        }
    }

    statusBar: StatusBar {
        RowLayout {
            anchors.fill: parent
            Label { 
                id: sbText
                text: "Welcome, please follow the steps"
            }
        }
    }

    // connection back to python
    Connections {
        target: skf

        // data from the download size, filename
        onDData: {
            lbImageComment.text = data
        }

        // receiving the percent of the download
        onDProg: {
            // make it visible if not already
            if (pbDownload.visible == false) {
                pbDownload.visible = true
            }

            // set percent
            if (percent > 0) {
                // set value
                pbDownload.indeterminate = false
                pbDownload.value = percent
            } else {
                // set indeterminate state
                pbDownload.indeterminate = true
            }
        }

        // download / local done
        onDDone: {
            // hide the buttons
            phDownloadButtons.visible = false
        }

        // show all buttons in the download and resize the windowds to it's original size
        onSStart: {
            pbDownload.visible = true
            pbDownload.value = 0
            phDownloadButtons.visible = true
            btBrowse.visible = true
            lbImageComment.text = ""
            sbText.text = ""
            btDown.visible = true
            btDown.text = "Download"
            btDown.tooltip = "Click here to download the base Skybian image from the official site"
            // hide other box placeholders
            boxNetwork.visible = false
            boxBuild.visible = false
        }

        // show network config
        onNetConfig: {
            // set next step visible
            boxNetwork.visible = true
        }

        // show build images config
        onBuildImages: {
            // set next step visible
            boxBuild.visible = true
        }

        // status bar messages
        onSetStatus: {
            sbText.text = msg
        }

        // on ok dialog
        onUiOk: {
            okDiag.title = title
            okDiag.text = text
            okDiag.open()
        }

        // on warn dialog
        onUiWarning: {
            warnDiag.title = title
            warnDiag.text = text
            warnDiag.open()
        }

        // on error dialog
        onUiError: {
            errorDiag.title = title
            errorDiag.text = text
            if (details != "") {
                errorDiag.detailedText = details
            } else {
                errorDiag.detailedText.visible = false
            }
            errorDiag.open()
        }

        // build data passing, hints to the user
        onBData: {
            lbBuild.text = data
        }

        // build single image progress
        onBsProg: {
            // make bars visible
            if (buildProgressBars.visible == false) {
                buildProgressBars.visible = true
            }

            // set percent
            if (percent > 0) {
                pbBuildSingle.value = percent
            }
        }

        // build overall image progress
        onBoProg: {
            // make bars visible
            if (buildProgressBars.visible == false) {
                buildProgressBars.visible = true
            }

            // set percent
            if (percent > 0) {
                pbBuildOverall.value = percent
            }
        }

        // hide the progress bars at the end of the build process
        onBFinished: {
            buildProgressBars.visible = false
            boxFlash.visible = true
            btBuild.enabled = false
        }

        // flash data percent
        onFsProg: {
            pbFlash.value = percent
        }
    }
}
