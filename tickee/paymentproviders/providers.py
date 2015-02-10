from tickee.paymentproviders import multisafepay, gcheckout
import gcheckout.provider
import multisafepay.provider

PAYMENT_PROVIDERS = {
    multisafepay.PROVIDER_NAME: multisafepay.provider.FastCheckoutPaymentProvider,
    gcheckout.PROVIDER_NAME: gcheckout.provider.GoogleCheckoutPaymentProvider
}