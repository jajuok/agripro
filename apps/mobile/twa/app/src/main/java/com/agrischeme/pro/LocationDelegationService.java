package com.agrischeme.pro;

import com.google.androidbrowserhelper.trusted.DelegationService;
import com.google.androidbrowserhelper.locationdelegation.LocationDelegationExtraCommandHandler;

public class LocationDelegationService extends DelegationService {
    public LocationDelegationService() {
        registerExtraCommandHandler(new LocationDelegationExtraCommandHandler());
    }
}
