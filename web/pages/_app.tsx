import type { AppProps } from "next/app"

export default function AIMod({ Component, pageProps: { session, ...pageProps } }: AppProps) {
    return (
        <Component {...pageProps} />
    )
}