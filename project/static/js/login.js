let user_id = "";

window.onload = () => {
    if (!localStorage["user_id"]) {
        initializeLiff("1655767329-J571PLN4");
    } else {
        user_id = localStorage["user_id"];
    }
}

function initializeLiff(myLiffId) {
    liff
        .init({
            liffId: myLiffId,
        })
        .then(() => {
            initializeApp();
        })
        .catch((err) => {
            console.log(err);
        });
}

function initializeApp() {
    if (!liff.isLoggedIn()) {
        liff.login()
    } else {
        liff.getProfile()
            .then((profile) => {
                user_id = profile.userId;
                localStorage["user_id"] = user_id;
            })
            .catch((err) => {
                console.log(err);
            });
    }
}

function Login() {
    LEETCODE_SESSION = document.getElementById("LEETCODE_SESSION").value;
    if (LEETCODE_SESSION == "") {
        Swal.fire({
            icon: "error",
            title: "錯誤",
            text: "LEETCODE_SESSION 欄位不得為空！",
            confirmButtonText: "關閉"
        })
    } else {
        let data = { LEETCODE_SESSION, user_id }

        const requestOptions = {
            method: 'POST',
            header: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
            mode: 'same-origin'
        };
        const requestURL = "/api/leetcode/login";

        Swal.fire({
            title: "查詢中，請稍候",
            didOpen: () => {
                Swal.showLoading()
                fetch(requestURL, requestOptions)
                    .then(response => response.json())
                    .then((data) => {
                        if (data.status == "success") {
                            Swal.fire({
                                icon: "success",
                                title: "成功",
                                text: data.message,
                                confirmButtonText: "關閉"
                            })
                                .then(() => {
                                    liff.closeWindow();
                                })
                        } else {
                            Swal.fire({
                                icon: "error",
                                title: "錯誤",
                                text: data.message,
                                confirmButtonText: "關閉"
                            })
                        }
                    })
                    .catch(error => {
                        console.log(error)
                        Swal.showValidationMessage(
                            "無法連接伺服器，請稍後再試！"
                        )
                    })
            },
        })
    }
}