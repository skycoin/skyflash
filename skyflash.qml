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
        id: aboutDialog
        title: "About Skyflash"
        text: "Skyflash is the official tool to create the\nSkyminers images from Skybian."
        onAccepted: visible = false
    }


    FileDialog {
        id: fileDialog
        title: "Please choose a file"
        folder: shortcuts.home
        nameFilters: ["System image files (*.img)"]
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
                onTriggered: aboutDialog.open()
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
            Label {
                text: "1. Get or select the Skybian base Image:"
                font.pixelSize: 14
                font.bold: true
                color: "black"
            }

            // buttons
            RowLayout {

                // Download button
                Button {
                    id: btDown
                    Layout.preferredHeight: 30
                    Layout.preferredWidth: 80
                    text: "Download"
                    tooltip: "Click here to download the base Skybian image from the official site"

                    onClicked: { skf.downloadSkybian() }
                }

                // Browse button
                Button {
                    id: btBrowse
                    Layout.preferredHeight: 30
                    Layout.preferredWidth: 80
                    text: "Browse"
                    tooltip: "Click here to browse a already downloaded Skybian image"

                    onClicked: { fileDialog.open() }
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
                value: 0.5
            }
        }

        // network box
        ColumnLayout {
            id: boxNetwork
            spacing: 10
            visible: false

            // box title
            Label {
                text: "2. Set network settings."
                font.pixelSize: 14
                font.bold: true
                color: "black"
            }

            // defaults CheckBox
            CheckBox {
                text: "Use skyminner defaults"
                checked: true

                onCheckedChanged: {
                    // TODO
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
                    maximumLength: 16

                }

                // dns
                Label { text: "Network DNS:" }

                TextField  {
                    id: txtDNS
                    Layout.preferredWidth: 200
                    placeholderText: "1.0.0.1, 1.1.1.1"
                    maximumLength: 34
                }

                // manager IP
                Label { text: "Manager IP:" }

                TextField {
                    id: txtManager
                    Layout.preferredWidth: 200
                    placeholderText: "192.168.0.2"
                    maximumLength: 16

                }

                // node count
                Label { text: "Node's count:" }

                TextField  {
                    id: txtNodes
                    Layout.preferredWidth: 200
                    placeholderText: "7"
                    maximumLength: 5
                }
            }
        }

        // build box
        ColumnLayout {
            id: boxBuild
            spacing: 10
            visible: false

            // box title
            Label {
                text: "3. Build the respective images."
                font.pixelSize: 14
                font.bold: true
                color: "black"
            }

            // build tools
            RowLayout {
                // build button
                Button {
                    id: btBuild
                    text: "Build the Images "

                    onClicked: {
                        // TODO
                    }
                }

                ProgressBar {
                    id: pbBuild
                    Layout.fillWidth: true
                    visible: true
                    maximumValue: 100
                    minimumValue: 0
                    value: 7
                }
            }
        }

        // flash box
        ColumnLayout {
            id: boxFlash
            spacing: 10
            visible: false

            // box title
            Label {
                text: "4. Flash the images."
                font.pixelSize: 14
                font.bold: true
                color: "black"
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
                    model: ListModel {
                        id: cbSdCardItems
                        ListElement { text: "Select..."; color: "Yellow" }
                        ListElement { text: "/dev/mmcblk0"; color: "Green" }
                        ListElement { text: "G:/"; color: "Brown" }
                    }
                    onCurrentIndexChanged: console.debug(cbSdCardItems.get(currentIndex).text + ", " + cbSdCardItems.get(currentIndex).color)
                }

                // flash ProgressBar
                ProgressBar {
                    id: pbFlash
                    Layout.fillWidth: true
                    visible: true
                    maximumValue: 100
                    minimumValue: 0
                    value: 88
                }
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
            pbDownload.value = percent
            sbText.text = "Downloaded " + Number(percent).toLocaleString(Qt.locale("en_US")) + "% so far"
        }

        // download / local done
        onDDone: {
            // inmediate actions
            lbImageComment.text = result

            // set next step visible
            boxNetwork.visible = true
            windows.height = 300

        }

        // status bar messages
        onSetStatus: {
            sbText.text = msg
        }
    }
}
