import QtQuick 2.9
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.0
import QtQuick.Dialogs 1.1

ApplicationWindow {
    id: windows
    width: 398
    //height: 420
    height: 148
    visible: true
    title: qsTr("Skyflash tool")

    // about dialog
    MessageDialog {
        id: aboutDiag
        title: "About Skyflash"
        text: "Skyflash is the official tool to create the\nSkyminers images from Skybian."
        onAccepted: visible = false
    }

    // generic warning dialog
    MessageDialog {
        id: warnDiag
        icon: StandardIcon.Warning
        title: ""
        text: ""
        onAccepted: {
            warnD.visible = false
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
                text: "Manual"
                onTriggered: skf.openManual()
            }

            MenuItem {
                text: "About..."
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
                    text: "1. Download it or browse a local Skybian release file:"
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
                visible: true
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
                text: "Use skyminner defaults"
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
                    } else {
                        // enable the fields for edit
                        txtGateway.enabled = true
                        txtDNS.enabled = true
                        txtManager.enabled = true
                        txtNodes.enabled = true
                    }
                }
            }

            // gateway
            GridLayout {
                columns: 2
                rows: 4

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
                Label { text: "Node's count:" }

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
                    text: "Build the Images "

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

            // particular image progress
            RowLayout{
                Label {
                    text: "Single image progress:"
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
                    text: "Overall progress:"
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

        // flash box
        ColumnLayout {
            id: boxFlash
            spacing: 10
            visible: true

            // box title
            Rectangle {
                Layout.fillWidth: true
                width: parent.width
                height: 22
                color: "lightblue"
                radius: 3

                Label {
                    text: "4. Flash the images."
                    font.pixelSize: 14
                    font.bold: true
                    color: "black"
                }
            }

            // flash tools
            RowLayout {
                // pick your uSD
                Label {
                    id: lbSdCard
                    text: "SD card:"
                }

                // ComboBox uSD
                ComboBox {
                    id: cbSdCard
                    currentIndex: 0
                    model: skf.cards
                    Layout.preferredHeight: 30
                    Layout.preferredWidth: 200

                    onCurrentTextChanged: {
                        console.debug("Actual Text is " + currentText)
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

                // Start Flashing!
                Button {
                    id: btFlash
                    Layout.preferredHeight: 30
                    Layout.preferredWidth: 120
                    enabled: false
                    text: "Start Flashing"
                    tooltip: "Click here to start flashing the cards with the built images"

                    onClicked: {
                        // call skyflash to flash the images
                        skf.imageFlash()
                    }
                }
            }

            Label {
                id: lbFlash
                text: ""
            }

            // flash ProgressBar
            ProgressBar {
                id: pbFlash
                Layout.fillWidth: true
                visible: true
                maximumValue: 100
                minimumValue: 0
                value: 0
            }

            // flash ProgressBar
            ProgressBar {
                id: pbFlashOverall
                Layout.fillWidth: true
                visible: true
                maximumValue: 100
                minimumValue: 0
                value: 0
            }
        }
    }

    statusBar: StatusBar {
        RowLayout {
            anchors.fill: parent
            Label { 
                id: sbText
                text: "Welcomed, please follow the steps"
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
            if (percent > 0) {
                pbDownload.indeterminate = false
                pbDownload.value = percent
            } else {
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
            // TODO resize windows
            windows.width = 398
            windows.height = 148
            // hide other box placeholders
            boxNetwork.visible = false
            boxBuild.visible = false
        }

        // show network config
        onNetConfig: {
            // set next step visible
            boxNetwork.visible = true
            windows.height = 300
        }

        // show build images config
        onBuildImages: {
            // set next step visible
            boxBuild.visible = true
            windows.height = 360
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
            if (percent > 0) {
                pbBuildSingle.value = percent
            }
        }

        // build overall image progress
        onBoProg: {
            if (percent > 0) {
                pbBuildOverall.value = percent
            }
        }

        // flash data passing, hints to the user
        onFData: {
            lbFlash.text = data
        }
    }
}
