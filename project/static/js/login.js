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
        user_id = "123"
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
                                text: "已成功登入帳號！",
                                confirmButtonText: "關閉"
                            })
                                .then(() => {
                                    console.log("close")
                                })
                        } else {
                            Swal.fire({
                                icon: "error",
                                title: "錯誤",
                                text: "登入失敗，請重新確認！",
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