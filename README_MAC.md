# macOS 배포 파일 만들기

중요: Windows에 있는 이 소스 폴더에는 `ScoreCapture.app`이 없습니다.
`ScoreCapture.app`은 macOS에서 빌드가 끝난 뒤 생성되는 결과물입니다.

초보 지인에게 전달할 파일은 소스 코드가 아니라 아래 둘 중 하나입니다.

```text
ScoreCapture-macOS.dmg
ScoreCapture-macOS.zip
```

## Windows 사용자가 만드는 방법

Windows에서는 macOS 실행파일을 직접 만들 수 없습니다.
대신 GitHub Actions가 macOS 컴퓨터에서 자동으로 빌드하게 하면 됩니다.

1. 이 프로젝트를 GitHub 저장소에 올립니다.
2. GitHub 저장소에서 `Actions` 탭을 엽니다.
3. `Build macOS app`을 선택합니다.
4. `Run workflow`를 누릅니다.
5. 빌드가 끝나면 `Artifacts`에서 `ScoreCapture-macOS`를 다운로드합니다.
6. 다운로드한 파일 안에 `ScoreCapture-macOS.dmg`와 `ScoreCapture-macOS.zip`이 있습니다.
7. 지인에게는 `ScoreCapture-macOS.dmg` 하나만 보내면 됩니다.

## 지인이 실행하는 방법

지인이 `ScoreCapture-macOS.dmg`를 받은 뒤:

1. `ScoreCapture-macOS.dmg`를 더블클릭합니다.
2. 열린 창 안의 `ScoreCapture.app`을 실행합니다.
3. 화면 기록 권한을 묻거나 설정이 열리면 `ScoreCapture`를 허용합니다.
4. 앱을 완전히 종료한 뒤 다시 실행합니다.

Apple Developer 계정으로 서명/공증하지 않은 앱은 macOS가 "확인되지 않은 개발자"라고 막을 수 있습니다.
그 경우 `ScoreCapture.app`을 Control 키를 누른 채 클릭하고 `열기`를 선택해야 합니다.

## 결과물 위치

캡처 이미지와 PDF는 지인의 Mac에서 아래 폴더에 저장됩니다.

```text
~/Documents/ScoreCapture
```

최종 PDF 파일명은 다음과 같습니다.

```text
final_sheet_music_stitched.pdf
```

## macOS 컴퓨터에서 직접 빌드할 때

Mac을 빌릴 수 있다면 터미널에서 아래 명령으로 직접 만들 수도 있습니다.

```bash
chmod +x build_macos.sh
./build_macos.sh
```

빌드가 끝나면 아래 파일들이 생깁니다.

```text
dist/ScoreCapture-macOS.zip
dist/ScoreCapture-macOS.dmg
```
